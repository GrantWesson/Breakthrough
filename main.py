import streamlit as st
import numpy as np

# --- FRACTAL ENCODER WITH N(0) OUTPUT ---
class NextGenFractalEncoder:
    def __init__(self, base_block_size=16):
        self.glyph_dict = {}
        self.next_glyph_id = 0
        self.last_glyph = (0.5, 0.5, 0.5)
        self.base_block_size = base_block_size

    def _bijective_seed(self, block: bytes):
        h = int.from_bytes(block, 'little')
        mask = (1 << 24) - 1
        x = ((h & mask)/mask + self.last_glyph[0]) % 1.0
        y = (((h >> 24) & mask)/mask + self.last_glyph[1]) % 1.0
        z = (((h >> 48) & mask)/mask + self.last_glyph[2]) % 1.0
        self.last_glyph = (x, y, z)
        return (x, y, z)

    def _recursive_encode_all(self, block: bytes):
        n = len(block)
        if n <= self.base_block_size:
            glyph = self._bijective_seed(block)
            key = tuple(int(g*255) for g in glyph)
            if key not in self.glyph_dict:
                self.glyph_dict[key] = self.next_glyph_id
                self.next_glyph_id += 1
            return [glyph]
        else:
            mid = n // 2
            left_glyphs = self._recursive_encode_all(block[:mid])
            right_glyphs = self._recursive_encode_all(block[mid:])
            merged_glyphs = []

            for lg, rg in zip(left_glyphs, right_glyphs):
                lx, ly, lz = lg
                rx, ry, rz = rg
                merged = (
                    (lx + rx + self.last_glyph[0]) / 3 % 1.0,
                    (ly + ry + self.last_glyph[1]) / 3 % 1.0,
                    (lz + rz + self.last_glyph[2]) / 3 % 1.0
                )
                self.last_glyph = merged
                merged_glyphs.append(merged)

            # append any leftover glyphs
            if len(left_glyphs) > len(right_glyphs):
                merged_glyphs.extend(left_glyphs[len(right_glyphs):])
            elif len(right_glyphs) > len(left_glyphs):
                merged_glyphs.extend(right_glyphs[len(left_glyphs):])
            return merged_glyphs

    def encode_bytes(self, data: bytes, chunk_size=1024*1024):
        encoded = bytearray()
        for offset in range(0, len(data), chunk_size):
            chunk = data[offset:offset+chunk_size]
            glyph_list = self._recursive_encode_all(chunk)
            for glyph in glyph_list:
                for g in glyph:
                    encoded.append(int(g*255))
        return bytes(encoded)

# --- STREAMLIT UI ---
st.title("Random Fractal Encoder with N(0) Output")

input_choice = st.radio("Input type:", ["Upload File", "Random Data"])
raw_data = b""
if input_choice == "Upload File":
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file:
        raw_data = uploaded_file.read()
elif input_choice == "Random Data":
    size_mb = st.number_input("Size of random data (MB)", min_value=1, value=10)
    raw_data = np.random.randint(0, 256, size_mb*1024*1024, dtype=np.uint8).tobytes()

if st.button("Encode Fractal"):
    encoder = NextGenFractalEncoder()
    compressed_bytes = encoder.encode_bytes(raw_data)

    st.subheader("Metrics")
    st.write(f"Original size: {len(raw_data)/1024**2:.2f} MB")
    st.write(f"Compressed size: {len(compressed_bytes)/1024**2:.2f} MB")
    st.write(f"Compression ratio: {len(raw_data)/len(compressed_bytes):.2f}x")
    st.write(f"Total glyphs: {encoder.next_glyph_id}")

    st.subheader("Fractal N(0) Preview")
    preview_len = min(100, len(raw_data))
    preview_glyphs = []
    for offset in range(0, preview_len, encoder.base_block_size):
        block = raw_data[offset:offset+encoder.base_block_size]
        glyph_list = encoder._recursive_encode_all(block)
        for glyph in glyph_list:
            for g in glyph:
                preview_glyphs.append(int(g*255))
                if len(preview_glyphs) >= preview_len:
                    break
            if len(preview_glyphs) >= preview_len:
                break
        if len(preview_glyphs) >= preview_len:
            break

    st.text(bytes(preview_glyphs))

    st.download_button(
        label="Download .fractal",
        data=compressed_bytes,
        file_name="data_nextgen_n0.fractal",
        mime="application/octet-stream"
    )