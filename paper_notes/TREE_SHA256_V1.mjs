import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const legacyNativeSeparators = process.argv.includes(
  "--legacy-native-separators",
);
const requestedRoot = process.argv
  .slice(2)
  .find((argument) => argument !== "--legacy-native-separators");

if (!requestedRoot) {
  console.error(
    "Usage: node paper_notes/TREE_SHA256_V1.mjs [--legacy-native-separators] <directory>",
  );
  process.exit(2);
}

const root = path.resolve(requestedRoot);
const files = [];

function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath);
    } else if (entry.isFile()) {
      files.push(fullPath);
    }
  }
}

walk(root);

const rows = files
  .map((fullPath) => {
    const bytes = fs.readFileSync(fullPath);
    return {
      relativePath: legacyNativeSeparators
        ? path.relative(root, fullPath)
        : path.relative(root, fullPath).split(path.sep).join("/"),
      byteLength: bytes.length,
      fileSha256: crypto.createHash("sha256").update(bytes).digest("hex"),
    };
  })
  .sort((left, right) =>
    left.relativePath.localeCompare(right.relativePath, "en", {
      sensitivity: "variant",
    }),
  );

const treeHash = crypto.createHash("sha256");
for (const row of rows) {
  treeHash.update(
    `${row.relativePath}\\0${row.byteLength}\\0${row.fileSha256}\\n`,
    "utf8",
  );
}

console.log(
  JSON.stringify(
    {
      root: requestedRoot,
      algorithm: legacyNativeSeparators
        ? "TREE-SHA256-V1-LEGACY-NATIVE-PATHS"
        : "TREE-SHA256-V1",
      tree_sha256: treeHash.digest("hex"),
      file_count: rows.length,
      byte_count: rows.reduce((sum, row) => sum + row.byteLength, 0),
      first_path: rows[0]?.relativePath ?? null,
      last_path: rows.at(-1)?.relativePath ?? null,
    },
    null,
    2,
  ),
);
