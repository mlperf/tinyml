import tensorflow as tf
import os
import numpy as np
import argparse

import get_dataset as kws_data
import kws_util

if __name__ == '__main__':
  Flags, unparsed = kws_util.parse_command()

  converter = tf.lite.TFLiteConverter.from_saved_model(Flags.saved_model_path)
  converter.optimizations = [tf.lite.Optimize.DEFAULT]
  
  with open("quant_cal_idxs.txt") as fpi:
    cal_indices = [int(line) for line in fpi]
  cal_indices.sort()

  num_calibration_steps = len(cal_indices)

  _, _, ds_val = kws_data.get_training_data(Flags, val_cal_subset=True)
  ds_val = ds_val.unbatch().batch(1) 

  if False: # enable if you want to check the distribution of labels in the calibration set
    label_counts = {}
    for label in range(12):
      label_counts[label] = 0
    for _, label in ds_val.as_numpy_iterator():
      label_counts[label[0]] += 1
    for label in range(12):
      print(f"Cal set has {label_counts[label]} of label {label}")
    

  ds_iter = ds_val.as_numpy_iterator()
  def representative_dataset_gen():
    for _ in range(num_calibration_steps):
      next_input = next(ds_iter)[0]
      yield [next_input]
  
  converter.optimizations = [tf.lite.Optimize.DEFAULT]
  converter.representative_dataset = representative_dataset_gen
  converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
  converter.inference_input_type = tf.int8  # or tf.uint8; should match dat_q in eval_quantized_model.py
  converter.inference_output_type = tf.int8  # or tf.uint8

  tflite_quant_model = converter.convert()
  with open(Flags.tfl_file_name, "wb") as fpo:
    fpo.write(tflite_quant_model)

