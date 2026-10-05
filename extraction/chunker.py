"""Chunking: împarte textul în bucăți mici, cu suprapunere.

Taie pe linii (ca să nu rupă un rând de tabel la mijloc), apoi
împachetează liniile în chunks de ~chunk_size caractere, cu overlap.
"""


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        # dacă adăugând linia depășim chunk_size, închidem chunk-ul curent
        if current_len + len(line) + 1 > chunk_size and current:
            chunks.append("\n".join(current))

            # overlap: păstrăm ultimele linii (până la ~overlap caractere)
            keep: list[str] = []
            keep_len = 0
            for prev in reversed(current):
                if keep_len + len(prev) + 1 > overlap:
                    break
                keep.insert(0, prev)
                keep_len += len(prev) + 1

            current = keep
            current_len = keep_len

        current.append(line)
        current_len += len(line) + 1

    if current:
        chunks.append("\n".join(current))

    return chunks