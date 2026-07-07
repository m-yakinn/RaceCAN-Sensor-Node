from bms_simulator import create_lipo_3s
from bms_to_can import BMSToCANEncoder

bms     = create_lipo_3s(capacity_mah=2500)
encoder = BMSToCANEncoder()

bms.update_cells([3.75, 3.70, 3.72])
bms.update_current(5.0)
bms.update_temperature(40.0)
state = bms.update()

frames = encoder.encode(state, chemistry="lipo", capacity_mah=2500)
# Returns list of 6 dicts: {frame_id, dlc, data (bytes), signals (dict)}
from bms_to_can import BMSCANDecoder

decoder = BMSCANDecoder()
decoded = decoder.decode(0x201, raw_bytes)
# Returns: {'current_a': 5.0, 'soc_percent': 50, 'shutdown_signal': 0, 'system_state': 'NORMAL'}
