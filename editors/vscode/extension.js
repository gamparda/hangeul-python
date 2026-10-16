const vscode = require("vscode");
const { execFile } = require("node:child_process");
const translations = require("./translations.json");

function activate(context) {
  const diagnostics = vscode.languages.createDiagnosticCollection("hangeul-python");
  const output = vscode.window.createOutputChannel("한글 파이썬");
  const running = new Map();
  context.subscriptions.push(diagnostics, output, {
    dispose() {
      for (const child of running.values()) child.kill();
    }
  });

  async function check(document) {
    if (!document || document.languageId !== "hangeul-python" || document.isUntitled) return;
    if (!vscode.workspace.isTrusted) return;
    const key = document.uri.toString();
    const previous = running.get(key);
    if (previous) previous.kill();
    const version = document.version;
    const python = vscode.workspace.getConfiguration("hangeulPython", document.uri)
      .get("pythonPath", "python");
    const child = execFile(python, ["-m", "hangeul_python", "check", "--json", document.fileName],
      { encoding: "utf8", windowsHide: true, timeout: 20000, maxBuffer: 1024 * 1024,
        env: { ...process.env, PYTHONUTF8: "1" } },
      (error, stdout, stderr) => {
        if (running.get(key) !== child) return;
        running.delete(key);
        if (document.isClosed || document.version !== version) return;
        try {
          const items = JSON.parse(stdout);
          if (!Array.isArray(items)) throw new Error("잘못된 진단 응답");
          diagnostics.set(document.uri, items.map(item => {
            const start = new vscode.Position(Math.max(0, item.line - 1),
              Math.max(0, item.column - 1));
            const end = new vscode.Position(Math.max(start.line, item.end_line - 1),
              Math.max(start.character + 1, item.end_column - 1));
            const diagnostic = new vscode.Diagnostic(new vscode.Range(start, end),
              item.message, vscode.DiagnosticSeverity.Error);
            diagnostic.source = "한글 파이썬";
            return diagnostic;
          }));
        } catch {
          diagnostics.delete(document.uri);
          output.appendLine(stderr || String(error || "문법 검사 응답을 읽지 못했습니다"));
        }
      });
    running.set(key, child);
  }

  context.subscriptions.push(vscode.languages.registerCompletionItemProvider(
    { language: "hangeul-python" }, {
      provideCompletionItems() {
        return translations.map(entry => {
          const item = new vscode.CompletionItem(entry.korean, vscode.CompletionItemKind.Text);
          item.detail = entry.originals.join(", ");
          return item;
        });
      }
    }, "."));
  context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(document => {
    if (vscode.workspace.getConfiguration("hangeulPython", document.uri).get("checkOnSave")) {
      check(document);
    }
  }));
  context.subscriptions.push(vscode.workspace.onDidCloseTextDocument(document => {
    const key = document.uri.toString();
    const child = running.get(key);
    if (child) child.kill();
    running.delete(key);
    diagnostics.delete(document.uri);
  }));
  context.subscriptions.push(vscode.commands.registerCommand("hangeulPython.check", async () => {
    const document = vscode.window.activeTextEditor?.document;
    if (document && await document.save()) await check(document);
  }));
  context.subscriptions.push(vscode.commands.registerCommand("hangeulPython.run", async () => {
    const document = vscode.window.activeTextEditor?.document;
    if (!document || document.languageId !== "hangeul-python") return;
    if (!vscode.workspace.isTrusted) {
      vscode.window.showInformationMessage("현재 작업 영역을 신뢰한 뒤 실행할 수 있습니다.");
      return;
    }
    if (!await document.save()) return;
    const python = vscode.workspace.getConfiguration("hangeulPython", document.uri)
      .get("pythonPath", "python");
    const task = new vscode.Task({ type: "hangeul-python" }, vscode.TaskScope.Workspace,
      "한글 파이썬 실행", "한글 파이썬",
      new vscode.ProcessExecution(python, ["-m", "hangeul_python", "run", document.fileName],
        { env: { PYTHONUTF8: "1" } }));
    await vscode.tasks.executeTask(task);
  }));
}

module.exports = { activate };
