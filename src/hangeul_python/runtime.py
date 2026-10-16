"""Resolve Korean APIs to the original Python objects at runtime."""

from __future__ import annotations

import builtins
import __future__
import importlib
import inspect
import sys
import types
from typing import Any

from .catalog import Catalog

_MISSING = object()


class AttributeSlot:
    """An ephemeral assignment target; the user's object is never wrapped."""

    def __init__(self, runtime: Runtime, obj: Any, name: str):
        self.runtime, self.obj, self.name = runtime, obj, name

    @property
    def value(self):
        return self.runtime.getattr(self.obj, self.name)

    @value.setter
    def value(self, value):
        setattr(self.obj, self.runtime.attribute_name(self.obj, self.name), value)

    @value.deleter
    def value(self):
        delattr(self.obj, self.runtime.attribute_name(self.obj, self.name))


class Runtime:
    def __init__(self, catalog: Catalog | None = None):
        self.catalog = catalog or Catalog()
        self.callables: dict[int, tuple[object, dict[str, str]]] = {}
        self.modules: dict[int, tuple[types.ModuleType, dict]] = {}
        self._builtins: dict | None = None
        for name, mapping in self.catalog.api["builtin_keywords"].items():
            if hasattr(builtins, name):
                self.register_callable(getattr(builtins, name), mapping)

    def register_callable(self, fn, mapping):
        self.callables[id(fn)] = (fn, {korean: original for original, korean in mapping.items()})

    def bind_module(self, name: str):
        module = importlib.import_module(name)
        profile = self.catalog.api["modules"].get(name, {})
        self.modules[id(module)] = (module, profile)
        for member, mapping in profile.get("keywords", {}).items():
            if hasattr(module, member):
                self.register_callable(getattr(module, member), mapping)
        return module

    def profiles(self, obj):
        if isinstance(obj, types.ModuleType):
            pair = self.modules.get(id(obj))
            if pair and pair[0] is obj:
                yield pair[1]
            else:
                name = obj.__name__
                if name in self.catalog.api["modules"] and sys.modules.get(name) is obj:
                    yield self.catalog.api["modules"][name]
            return
        cls = obj if isinstance(obj, type) else type(obj)
        for base in cls.__mro__:
            for name in self.catalog.api["types"]:
                module_name, _, class_name = name.rpartition(".")
                module = sys.modules.get(module_name)
                if module is not None and vars(module).get(class_name) is base:
                    yield self.catalog.type_profile(name)

    def attribute_name(self, obj, name: str) -> str:
        if inspect.getattr_static(obj, name, _MISSING) is not _MISSING:
            return name
        for profile in self.profiles(obj):
            for original, korean in profile.get("members", {}).items():
                if name == korean:
                    return original
        return self.catalog.replacements.get(name, name)

    def getattr(self, obj, name: str, default=_MISSING):
        if obj is builtins and name in self.builtins():
            return self.builtins()[name]
        # Do not swallow AttributeError raised *inside* a real Korean descriptor.
        if inspect.getattr_static(obj, name, _MISSING) is not _MISSING:
            return (builtins.getattr(obj, name) if default is _MISSING
                    else builtins.getattr(obj, name, default))
        try:
            result = builtins.getattr(obj, name)
        except AttributeError:
            original = self.attribute_name(obj, name)
            if default is _MISSING:
                result = builtins.getattr(obj, original)
            else:
                result = builtins.getattr(obj, original, default)
        if isinstance(obj, types.ModuleType):
            original = self.attribute_name(obj, name)
            for profile in self.profiles(obj):
                if mapping := profile.get("keywords", {}).get(original):
                    self.register_callable(result, mapping)
        if isinstance(obj, types.ModuleType) and isinstance(result, types.ModuleType):
            for canonical, profile in self.catalog.api["modules"].items():
                if sys.modules.get(canonical) is result:
                    self.modules[id(result)] = (result, profile)
                    break
        return result

    def localized_getattr(self, obj, name, default=_MISSING):
        return self.getattr(obj, name, default)

    def localized_setattr(self, obj, name, value):
        return builtins.setattr(obj, self.attribute_name(obj, name), value)

    def localized_delattr(self, obj, name):
        return builtins.delattr(obj, self.attribute_name(obj, name))

    def localized_hasattr(self, obj, name):
        try:
            self.getattr(obj, name)
        except AttributeError:
            return False
        return True

    def localized_dir(self, obj=_MISSING):
        if obj is _MISSING:
            return sorted(sys._getframe(1).f_locals)
        names = set(builtins.dir(obj))
        for profile in self.profiles(obj):
            for original, korean in profile.get("members", {}).items():
                if original in names:
                    names.add(korean)
        for original, korean in self.catalog.core["special_names"].items():
            if original in names:
                names.add(korean)
        return sorted(names)

    def keyword_mapping(self, fn) -> dict[str, str]:
        pair = self.callables.get(id(fn))
        if pair and pair[0] is fn:
            return pair[1]
        # Bound methods are recreated on every attribute access. Resolve their owner.
        if isinstance(fn, (types.BuiltinMethodType, types.MethodType)):
            owner = fn.__self__
            for profile in self.profiles(owner):
                if mapping := profile.get("keywords", {}).get(fn.__name__):
                    return {korean: original for original, korean in mapping.items()}
        return {}

    def call(self, fn, /, *args, **kwargs):
        mapping = self.keyword_mapping(fn)
        translated = {}
        for key, value in kwargs.items():
            target = mapping.get(key, key)
            if target in translated:
                raise TypeError(f"인자 '{target}'에 값이 두 번 전달되었습니다")
            translated[target] = value
        caller = sys._getframe(1)
        # Keep frame-sensitive builtins in the source program's frame.
        if fn is builtins.globals and not args and not translated:
            return caller.f_globals
        if (fn is builtins.locals or fn is builtins.vars) and not args and not translated:
            return dict(caller.f_locals)
        if (fn is builtins.dir or self.is_method(fn, "localized_dir")) and not args and not translated:
            return sorted(caller.f_locals)
        if fn is builtins.super and not args and not translated:
            cls = caller.f_locals.get("__class__")
            if cls is None or not caller.f_code.co_argcount:
                raise RuntimeError("super(): no arguments")
            first = caller.f_code.co_varnames[0]
            return builtins.super(cls, caller.f_locals[first])
        if self.is_method(fn, "localized_eval") or self.is_method(fn, "localized_exec"):
            return self.dynamic(self.is_method(fn, "localized_eval"), caller, args, translated)
        if fn is builtins.eval or fn is builtins.exec:
            return self.dynamic(fn is builtins.eval, caller, args, translated, korean=False)
        return fn(*args, **translated)

    def is_method(self, fn, name):
        return isinstance(fn, types.MethodType) and fn.__self__ is self and (
            fn.__func__ is getattr(type(self), name)
        )

    def dynamic(self, expression: bool, frame, args, kwargs, *, korean=True):
        kwargs = dict(kwargs)
        names = ("source", "globals", "locals")
        if len(args) > 3:
            raise TypeError("평가/실행은 위치 인자를 최대 3개 받습니다")
        values = dict(zip(names, args, strict=False))
        for name in names:
            if name in kwargs:
                if name in values:
                    raise TypeError(f"인자 '{name}'에 값이 두 번 전달되었습니다")
                values[name] = kwargs.pop(name)
        if "source" not in values:
            raise TypeError("소스 인자가 필요합니다")
        globals_arg = values.get("globals")
        scope = frame.f_globals if globals_arg is None else globals_arg
        local = values.get("locals")
        if local is None:
            local = frame.f_locals if globals_arg is None else scope
        source = values["source"]
        if korean:
            self.prepare(scope)
            if isinstance(source, (str, bytes)):
                from .compiler import compile_source
                if isinstance(source, bytes):
                    source = source.decode("utf-8-sig")
                if expression:
                    source = source.lstrip(" \t")
                source = compile_source(source, "<한글 평가>" if expression else "<한글 실행>",
                                        mode="eval" if expression else "exec", runtime=self,
                                        flags=self.future_flags(frame))
        fn = builtins.eval if expression else builtins.exec
        return fn(source, scope, local, **kwargs)

    def localized_eval(self, /, *args, **kwargs):
        mapping = self.catalog.api["builtin_keywords"]["eval"]
        reverse = {v: k for k, v in mapping.items()}
        return self.dynamic(True, sys._getframe(1), args,
                            {reverse.get(k, k): v for k, v in kwargs.items()})

    def localized_exec(self, /, *args, **kwargs):
        mapping = self.catalog.api["builtin_keywords"]["exec"]
        reverse = {v: k for k, v in mapping.items()}
        return self.dynamic(False, sys._getframe(1), args,
                            {reverse.get(k, k): v for k, v in kwargs.items()})

    def localized_compile(self, source, filename, mode, flags=0, dont_inherit=False,
                          optimize=-1, **kwargs):
        from .compiler import compile_source
        frame = sys._getframe(1)
        if frame.f_code is type(self).call.__code__:
            frame = frame.f_back
        if not dont_inherit:
            flags |= self.future_flags(frame)
        if not isinstance(source, (str, bytes)):
            return builtins.compile(source, filename, mode, flags=flags,
                                    dont_inherit=True, optimize=optimize, **kwargs)
        if kwargs:
            # CPython's private _feature_version option is not part of the language API.
            raise TypeError(f"지원하지 않는 컴파일 인자: {', '.join(kwargs)}")
        if isinstance(source, bytes):
            source = source.decode("utf-8-sig")
        return compile_source(source, filename, mode=mode, runtime=self, flags=flags,
                              optimize=optimize)

    @staticmethod
    def future_flags(frame):
        mask = 0
        for name in __future__.all_feature_names:
            mask |= getattr(__future__, name).compiler_flag
        return frame.f_code.co_flags & mask

    def import_star(self, name: str, scope: dict):
        module = self.bind_module(name)
        exported = getattr(module, "__all__", None)
        for original, korean in self.catalog.api["modules"].get(name, {}).get("members", {}).items():
            if (exported is None or original in exported) and hasattr(module, original):
                scope[korean] = getattr(module, original)

    def builtins(self) -> dict:
        if self._builtins is not None:
            return self._builtins
        result = vars(builtins).copy()
        for section in ("builtins", "exceptions"):
            for original, korean in self.catalog.core[section].items():
                if hasattr(builtins, original):
                    result[korean] = getattr(builtins, original)
        for original, implementation in {
            "getattr": self.localized_getattr, "setattr": self.localized_setattr,
            "delattr": self.localized_delattr, "hasattr": self.localized_hasattr,
            "dir": self.localized_dir, "eval": self.localized_eval, "exec": self.localized_exec,
            "compile": self.localized_compile,
        }.items():
            result[self.catalog.core["builtins"][original]] = implementation
            self.register_callable(implementation,
                                   self.catalog.api["builtin_keywords"].get(original, {}))
        result.update({
            "__han_getattr__": self.getattr,
            "__han_target__": lambda obj, name: AttributeSlot(self, obj, name),
            "__han_call__": self.call,
            "__han_bind_module__": self.bind_module,
            "__han_import_star__": self.import_star,
            "__han_globals__": builtins.globals,
        })
        self._builtins = result
        return result

    def prepare(self, namespace: dict):
        namespace.setdefault("__name__", "__main__")
        namespace["__builtins__"] = self.builtins()
        return namespace


def export_namespace(profile=None) -> dict:
    from .importer import import_context
    catalog = Catalog()
    if profile:
        catalog.apply_profile(profile)
    runtime = Runtime(catalog)
    all_builtins = runtime.builtins()
    names = {key: value for key, value in all_builtins.items()
             if key not in vars(builtins) or key.startswith("__han_")}
    return {"__builtins__": all_builtins,
            "__han_import_context__": lambda: import_context(runtime), **names}
