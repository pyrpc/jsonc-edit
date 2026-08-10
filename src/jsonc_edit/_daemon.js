const readline = require('readline');
const fs = require('fs');
const path = require('path');

// Read the jsonc-parser path from CLI args
const parserPath = process.argv[2];
if (!parserPath) {
    console.error("Missing jsonc-parser path argument");
    process.exit(1);
}

// Ensure the module exists (basic check)
if (!fs.existsSync(parserPath)) {
    console.error(`Cannot find jsonc-parser at ${parserPath}`);
    process.exit(1);
}

let jsoncParser;
try {
    jsoncParser = require(parserPath);
} catch (err) {
    console.error(`Failed to load jsonc-parser from ${parserPath}: ${err.message}`);
    process.exit(1);
}

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

function send(msg) {
    process.stdout.write(JSON.stringify(msg) + '\n');
}

rl.on('line', (line) => {
    if (!line.trim()) return;

    let req;
    try {
        req = JSON.parse(line);
    } catch (e) {
        send({ success: false, error: "Malformed JSON" });
        return;
    }

    try {
        if (req.op === "ping") {
            send({ success: true, data: "pong" });
        } else if (req.op === "modify") {
            const { text, path, value, options } = req.args;
            const edits = jsoncParser.modify(text, path, value, options || {});
            send({ success: true, data: edits });
        } else if (req.op === "apply_edits") {
            const { text, edits } = req.args;
            const newText = jsoncParser.applyEdits(text, edits);
            send({ success: true, data: newText });
        } else if (req.op === "get_value") {
            const { text, path } = req.args;
            const tree = jsoncParser.parseTree(text);
            const node = jsoncParser.findNodeAtLocation(tree, path);
            if (node === undefined) {
                send({ success: true, data: { found: false } });
            } else {
                send({ success: true, data: { found: true, value: jsoncParser.getNodeValue(node) } });
            }
        } else {
            send({ success: false, error: `Unknown operation: ${req.op}` });
        }
    } catch (e) {
        send({ success: false, error: e.message, type: 'ParseError' });
    }
});
