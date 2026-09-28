from pathlib import Path
import argparse
import hashlib
import json
import re
import struct
import subprocess


SOURCE_SUFFIX = "muse-research-archive-2026-09-26/phase-two/corrected/catalog-phase2-2026-09-26-v2/code-snippets"
WINDOWS = ("window-0x4a98f0-0x4aab7e.txt", "window-0x48e5c0-0x48e976.txt", "window-0x4a7600-0x4a7a79.txt", "window-0x4bc7f0-0x4bc9fd.txt")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(text):
    result = []
    for line in text.splitlines():
        match = re.match(r"^\s*(?:0x)?([0-9a-f]+):\s+((?:[0-9a-f]{2}(?:\s+|$))+)(.*)$", line)
        if not match:
            continue
        address, data, assembly = int(match[1], 16), bytes.fromhex(match[2]), match[3].strip()
        if assembly:
            result.append({"address": address, "bytes": data, "assembly": assembly})
        else:
            assert result and address == result[-1]["address"] + len(result[-1]["bytes"])
            result[-1]["bytes"] += data
    return result


def wrap_elf(data, base):
    names = b"\0.text\0.shstrtab\0"
    names_offset = 64 + len(data)
    section_offset = (names_offset + len(names) + 7) & ~7
    ident = b"\x7fELF\x02\x01\x01" + b"\0" * 9
    header = struct.pack("<16sHHIQQQIHHHHHH", ident, 1, 62, 1, 0, 0, section_offset, 0, 64, 0, 0, 64, 3, 2)
    sections = b"\0" * 64
    sections += struct.pack("<IIQQQQIIQQ", 1, 1, 6, base, 64, len(data), 0, 0, 1, 0)
    sections += struct.pack("<IIQQQQIIQQ", 7, 3, 0, 0, names_offset, len(names), 0, 0, 1, 0)
    prefix = header + data + names
    return prefix + b"\0" * (section_offset - len(prefix)) + sections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    source_dir = source_root / SOURCE_SUFFIX
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    version = subprocess.run(["/usr/bin/objdump", "--version"], capture_output=True, text=True, check=True).stdout
    results = []
    for filename in WINDOWS:
        source = source_dir / filename
        original = source.read_bytes()
        supplied = rows(original.decode())
        start, end = [int(value, 16) for value in re.findall(r"0x([0-9a-f]+)", filename)]
        assert supplied[0]["address"] == start
        assert supplied[-1]["address"] + len(supplied[-1]["bytes"]) == end
        assert all(a["address"] + len(a["bytes"]) == b["address"] for a, b in zip(supplied, supplied[1:]))
        data = b"".join(row["bytes"] for row in supplied)
        assert len(data) == end - start
        stem = source.stem
        (output / (stem + ".bytes-from-text.bin")).write_bytes(data)
        elf = output / (stem + ".constructed.elf")
        elf.write_bytes(wrap_elf(data, start))
        command = ["/usr/bin/objdump", "--disassemble", "--disassemble-zeroes", "--x86-asm-syntax=intel", str(elf)]
        run = subprocess.run(command, capture_output=True, text=True)
        (output / (stem + ".llvm.txt")).write_text(run.stdout)
        (output / (stem + ".stderr.txt")).write_text(run.stderr)
        assert run.returncode == 0, run.stderr
        decoded = rows(run.stdout)
        expected = {row["address"]: row["bytes"] for row in supplied}
        actual = {row["address"]: row["bytes"] for row in decoded}
        differences = [hex(address) for address in sorted(expected.keys() | actual.keys()) if expected.get(address) != actual.get(address)]
        assert source.read_bytes() == original
        results.append({"source": source.relative_to(source_root).as_posix(), "source_text_sha256": digest(original), "start": hex(start), "end_exclusive": hex(end), "bytes_extracted_from_supplied_text": len(data), "extracted_bytes_sha256": digest(data), "supplied_instruction_count": len(supplied), "local_instruction_count": len(decoded), "address_byte_differences": differences, "all_bytes_decoded": b"".join(row["bytes"] for row in decoded) == data, "argv": command, "exit_code": run.returncode})
    report = {"author": "Astra (gpt-6-astra)", "method": "Extract byte columns from existing supplied text dumps, wrap as local ELF objects, decode with installed LLVM. No supplied code is executed.", "decoder_version": version.splitlines()[0], "limits": ["Checks internal consistency of supplied byte columns and instruction boundaries, not independent remote provenance.", "These are bytes reconstructed from text already held locally, not newly acquired client code or a full executable.", "Semantic annotations and pseudocode require separate review."], "windows": results, "total_bytes": sum(row["bytes_extracted_from_supplied_text"] for row in results), "total_instructions": sum(row["local_instruction_count"] for row in results), "all_match": all(not row["address_byte_differences"] and row["all_bytes_decoded"] for row in results)}
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("total_bytes", "total_instructions", "all_match")}))


if __name__ == "__main__":
    main()
