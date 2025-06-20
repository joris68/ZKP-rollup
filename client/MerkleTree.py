import hashlib

class MerkleTree:
    def __init__(self, leaves: list[bytes]):
        n = 1
        while n < len(leaves):
            n <<= 1
        leaves = leaves + [b'\x00' * 32] * (n - len(leaves))
        self.levels = [leaves]
        self._build()

    def _build(self):
        lvl = self.levels[0]
        while len(lvl) > 1:
            nxt = []
            for i in range(0, len(lvl), 2):
                nxt.append(hashlib.sha256(lvl[i] + lvl[i + 1]).digest())
            self.levels.insert(0, nxt)
            lvl = nxt

    @property
    def root(self) -> bytes:
        return self.levels[0][0]

    def get_proof(self, idx: int) -> tuple[list[int], list[bytes]]:
        proof = []
        dirs = []
        for lvl in range(len(self.levels) - 1, 0, -1):
            sib = idx ^ 1
            dirs.append(1 if (idx % 2) == 1 else 0)
            proof.append(self.levels[lvl][sib])
            idx //= 2
        return dirs, proof
