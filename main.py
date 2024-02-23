
import time
import struct

from pce_bph20 import pce_bph20



if __name__ == "__main__":

    ph_meter = pce_bph20()
    ph_meter.enable_data_logging()                  # special message needs to be sent to start data logging
    time.sleep(1)                                   # give some time to the device to start collecting data

    print("START")
    ph_meter.start_collecting_data()
    time.sleep(6)

    for i in range(5):
        sensor_data = ph_meter.get_sensor_data()
        print(sensor_data)

















    ph_meter.stop_collecting_data()


    # for n in range(1,10):
    #
    #     print("reading data attempt " + str(n))
    #
    #     for i in range(1,15):
    #         time.sleep(.5)
    #         ph_meter.get_data_to_buffer()
    #
    #     print(ph_meter.data_buffer)
    #
    #     ph_meter.decode_data_packet()
    #     time.sleep(1)
    #     ph_meter.decode_data_packet()
    #     time.sleep(1)
    #     ph_meter.decode_data_packet()
    #
    #
    #
    #
    # ph_meter.disable_data_logging()
    #
    #
    # # ph_meter.get_sensor_data()
    #
    # # Define the format string based on the provided structure
    # format_string = "<4B 4B 4B 2B 2B B B B B 2B 2B B B B B 2B 2B f f f f f f f f f f f f f f f f 8B B B B 5B"
    #
    # # # Replace 'data' with your actual binary data received from the device
    # # # You should read the data from the serial port or another source
    # # data = b'\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0\x12\x34\x56\x78\x9A\xBC\xDE\xF0'
    # #
    # # # Unpack the data based on the format string
    # # unpacked_data = struct.unpack(format_string, data)
    #
    # # # Assign unpacked values to variables based on the structure
    # # (
    # #     model, cmd, cond_unit, cond_mode, cond_resolution, ph_tmp_src, cond_tmp_src,
    # #     do_tmp_src, cond_std_type, ph_std_type, ph_h2o_type, tmp_unit, is_ph_stable,
    # #     is_cond_stable, is_do_stable, ph_resolution, do_resolution, ph_val, mv_val,
    # #     ph_tmp_val, cond_val, cond_tmp_val, do_val, do_sat_val, do_tmp_val, do_current,
    # #     ph_mtc_tmp, cond_mtc_tmp, do_mtc_tmp, cond_tmp_comp_coe, cond_tds_coe,
    # #     cond_electrode_const, do_pressure_comp_val, do_salinity_comp_val, is_ph_atc,
    # #     is_cond_atc, is_do_atc, cond_ref_tmp
    # # ) = unpacked_data

    print("END")

