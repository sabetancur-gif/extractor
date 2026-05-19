/* global PEO */
/* zip.js — construcción de archivos ZIP (STORE, sin compresión) */
"use strict";

const _CRC32_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    t[i] = c;
  }
  return t;
})();

function _crc32(data) {
  let c = 0xFFFFFFFF;
  for (const b of data) c = _CRC32_TABLE[(c ^ b) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

PEO.buildZip = function(entries) {
  const enc = new TextEncoder();
  const locals = [], central = [];
  let offset = 0;

  for (const { name, data } of entries) {
    const nb = enc.encode(name);
    const crc = _crc32(data);
    const size = data.length;

    const lfh = new Uint8Array(30 + nb.length);
    const lfv = new DataView(lfh.buffer);
    lfv.setUint32(0, 0x04034B50, true); lfv.setUint16(4, 20, true);
    lfv.setUint16(6, 0, true);          lfv.setUint16(8, 0, true);
    lfv.setUint16(10, 0, true);         lfv.setUint16(12, 0, true);
    lfv.setUint32(14, crc, true);       lfv.setUint32(18, size, true);
    lfv.setUint32(22, size, true);      lfv.setUint16(26, nb.length, true);
    lfv.setUint16(28, 0, true);         lfh.set(nb, 30);
    locals.push(lfh, data);

    const cde = new Uint8Array(46 + nb.length);
    const cdv = new DataView(cde.buffer);
    cdv.setUint32(0, 0x02014B50, true); cdv.setUint16(4, 20, true);
    cdv.setUint16(6, 20, true);         cdv.setUint16(8, 0, true);
    cdv.setUint16(10, 0, true);         cdv.setUint16(12, 0, true);
    cdv.setUint16(14, 0, true);         cdv.setUint32(16, crc, true);
    cdv.setUint32(20, size, true);      cdv.setUint32(24, size, true);
    cdv.setUint16(28, nb.length, true); cdv.setUint16(30, 0, true);
    cdv.setUint16(32, 0, true);         cdv.setUint16(34, 0, true);
    cdv.setUint16(36, 0, true);         cdv.setUint32(38, 0, true);
    cdv.setUint32(42, offset, true);    cde.set(nb, 46);
    central.push(cde);

    offset += lfh.length + data.length;
  }

  const cdOffset = offset;
  const cdSize   = central.reduce((s, c) => s + c.length, 0);
  const eocd = new Uint8Array(22);
  const ev   = new DataView(eocd.buffer);
  ev.setUint32(0, 0x06054B50, true);      ev.setUint16(4, 0, true);
  ev.setUint16(6, 0, true);               ev.setUint16(8, entries.length, true);
  ev.setUint16(10, entries.length, true); ev.setUint32(12, cdSize, true);
  ev.setUint32(16, cdOffset, true);       ev.setUint16(20, 0, true);

  const all   = [...locals, ...central, eocd];
  const total = all.reduce((s, p) => s + p.length, 0);
  const zip   = new Uint8Array(total);
  let pos = 0;
  for (const p of all) { zip.set(p, pos); pos += p.length; }
  return zip;
};

PEO.downloadZip = function(entries, zipName) {
  const zipBytes = PEO.buildZip(entries);
  const url = URL.createObjectURL(new Blob([zipBytes], { type: "application/zip" }));
  const a   = document.createElement("a");
  a.href = url; a.download = zipName; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
};
