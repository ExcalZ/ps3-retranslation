// Run with: node tools/test_webpatch_smd.js
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "release", "patcher_template.html"), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const element = () => ({ addEventListener() {}, appendChild() {} });
const context = { document: { getElementById: element, createElement: element }, window: {}, atob };
vm.runInNewContext(script, context);

for (const length of [786432, 789624, 4194304]) {
  const bin = new Uint8Array(length);
  for (let i = 0; i < bin.length; i++) bin[i] = (i * 37 + 13) & 0xff;
  const smd = context.window.__binToSmd(bin);
  const paddedLength = Math.ceil(length / 16384) * 16384;
  assert.equal(smd.length, 512 + paddedLength);
  assert.equal(smd[0], (paddedLength / 16384) & 0xff);
  assert.equal(smd[8], 0xaa);
  assert.equal(smd[9], 0xbb);
  assert.equal(smd[10], 0x06);
  assert.equal(vm.runInNewContext("isSmd", context)(smd), true);

  const decoded = vm.runInNewContext("smdToBin", context)(smd);
  assert.deepEqual(Buffer.from(decoded.subarray(0, length)), Buffer.from(bin));
  assert.ok(decoded.subarray(length).every(byte => byte === 0xff));
}

console.log("SMD conversion preserves the ROM and pads the final block");

// Exercise each packaged patcher against its recorded output hash.
const releaseDir = path.join(root, "release");
const stock = path.join(root, "PSIII_Disasm", "ps3original.bin");
for (const name of fs.readdirSync(releaseDir).filter(name => /^PS3_Retranslation_v[\d.]+$/.test(name))) {
  const page = path.join(releaseDir, name, "Patcher.html");
  if (!fs.existsSync(page) || !fs.existsSync(stock)) continue;
  const releaseScript = fs.readFileSync(page, "utf8").match(/<script>([\s\S]*?)<\/script>/)[1];
  const readme = fs.readFileSync(path.join(path.dirname(page), "readme.txt"), "utf8");
  const outputInfo = readme.split("The patched ROM:")[1];
  const expectedLength = Number(outputInfo.match(/Size:\s+([\d,]+) bytes/)[1].replaceAll(",", ""));
  const expectedSha1 = outputInfo.match(/SHA-1:\s+([A-F0-9]+)/)[1].toLowerCase();
  const releaseContext = { document: context.document, window: {}, atob };
  vm.runInNewContext(releaseScript, releaseContext);
  const source = Uint8Array.from(fs.readFileSync(stock));
  const { bin } = releaseContext.window.__patchBuffer(source.buffer, "ps3original.bin");
  assert.equal(bin.length, expectedLength);
  assert.equal(crypto.createHash("sha1").update(bin).digest("hex"), expectedSha1);
  const sourceSmd = releaseContext.window.__binToSmd(source);
  const fromSmd = releaseContext.window.__patchBuffer(sourceSmd.buffer, "ps3original.smd");
  assert.equal(fromSmd.smd, true);
  assert.deepEqual(Buffer.from(fromSmd.bin), Buffer.from(bin));
  const smd = releaseContext.window.__binToSmd(bin);
  assert.equal(smd.length, 512 + Math.ceil(bin.length / 16384) * 16384);
  const decoded = vm.runInNewContext("smdToBin", releaseContext)(smd);
  assert.deepEqual(Buffer.from(decoded.subarray(0, bin.length)), Buffer.from(bin));
  assert.ok(decoded.subarray(bin.length).every(byte => byte === 0xff));
  console.log(`${name} patcher produces the expected ROM in BIN and SMD formats`);
}
