using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text.Json;

// Read-only metadata audit. Matching debug metadata is not deployment wiring.
if (args.Length != 2) throw new ArgumentException("usage: audit assembly.dll assembly.pdb");
byte[] peBytes = File.ReadAllBytes(args[0]), pdbBytes = File.ReadAllBytes(args[1]);
using var pe = new PEReader(new MemoryStream(peBytes, false));
using var provider = MetadataReaderProvider.FromPortablePdbStream(new MemoryStream(pdbBytes, false));
var metadata = provider.GetMetadataReader();
var id = metadata.DebugMetadataHeader!.Id.ToArray();
if (id.Length != 20) throw new InvalidDataException("unexpected portable PDB content ID");
var pdbGuid = new Guid(id.AsSpan(0, 16));
uint pdbStamp = System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(id.AsSpan(16, 4));
// Portable PDB checksums use content with the 20-byte content ID zeroed.
byte[] normalizedPdb = (byte[])pdbBytes.Clone();
Array.Clear(normalizedPdb, metadata.DebugMetadataHeader.IdStartOffset, 20);
var codeViews = new List<object>();
bool identityMatch = false, checksumPresent = false, checksumMatch = true;
foreach (var entry in pe.ReadDebugDirectory()) {
    if (entry.Type == DebugDirectoryEntryType.CodeView) {
        var cv = pe.ReadCodeViewDebugDirectoryData(entry);
        bool matches = cv.Guid == pdbGuid && entry.Stamp == pdbStamp && cv.Age == 1;
        identityMatch |= matches;
        codeViews.Add(new { guid = cv.Guid, stamp = entry.Stamp, age = cv.Age, path = cv.Path, matches });
    }
    if (entry.Type == DebugDirectoryEntryType.PdbChecksum) {
        checksumPresent = true;
        var checksum = pe.ReadPdbChecksumDebugDirectoryData(entry);
        byte[] actual = checksum.AlgorithmName switch {
            "SHA256" => SHA256.HashData(normalizedPdb),
            "SHA1" => SHA1.HashData(normalizedPdb),
            _ => throw new InvalidDataException("unsupported PE PDB checksum algorithm")
        };
        checksumMatch &= actual.AsSpan().SequenceEqual(checksum.Checksum.AsSpan());
    }
}
var documents = new List<object>();
foreach (var handle in metadata.Documents) {
    var document = metadata.GetDocument(handle);
    var algorithm = metadata.GetGuid(document.HashAlgorithm);
    var hash = metadata.GetBlobBytes(document.Hash);
    documents.Add(new { name = metadata.GetString(document.Name), algorithm = algorithm.ToString(),
                       checksum = Convert.ToHexString(hash).ToLowerInvariant() });
}
var result = new {
    schema = "crane-portable-pdb-metadata-audit/v1", assembly = Path.GetFullPath(args[0]),
    pdb = Path.GetFullPath(args[1]), assembly_sha256 = Convert.ToHexString(SHA256.HashData(peBytes)).ToLowerInvariant(),
    pdb_sha256 = Convert.ToHexString(SHA256.HashData(pdbBytes)).ToLowerInvariant(),
    pdb_guid = pdbGuid, pdb_stamp = pdbStamp, code_views = codeViews,
    assembly_pdb_identity_match = identityMatch, pe_pdb_checksum_present = checksumPresent,
    pe_pdb_checksum_match = checksumPresent ? (bool?)checksumMatch : null,
    documents, deployment_wiring_proven = false
};
Console.WriteLine(JsonSerializer.Serialize(result));
return identityMatch && checksumMatch ? 0 : 2;
