import struct
import numpy

# https://github.com/NTNU-SmallSat-Lab/onboard-pipeline-modules/tree/classification/decoding

file_path = 'labels.bin'

# Functions that analyse the binary file generated by the SVMBDT
# and converts it to a readable execution [int], n_classes[], and
# the predicted labels[].

with open(file_path, mode='rb') as file:  # b is important -> binary
    fileContent = file.read()
filesize = len(fileContent)
unpack_opt = "ii16B" + str(filesize - 4 - 4 - 16) + "B"
arr = struct.unpack(unpack_opt, fileContent)
classification_execution_time = arr[0]
loading_execution_time = arr[1]
classes_holder = arr[2:18]
labels_holder = arr[18:]

classes = []
labels = []

# Decode the labels and converts
# them back to original classes.

for i in range(len(classes_holder)):
    if (int(classes_holder[i]) != 255):
        classes.append(classes_holder[i])

if (len(classes) <= 2):
    for i in range(len(labels_holder)):
        pixel_str = format(labels_holder[i], "b").zfill(8)
        for j in range(8):
            labels.append(int(pixel_str[j], 2))

if (len(classes) > 2 and len(classes) <= 4):
    for i in range(len(labels_holder)):
        pixel_str = format(labels_holder[i], "b").zfill(8)
        for j in range(4):
            labels.append(int(pixel_str[2 * j:(j + 1) * 2], 2))

if (len(classes) > 4 and len(classes) <= 16):
    for i in range(len(labels_holder)):
        pixel_str = format(labels_holder[i], "b").zfill(8)
        for j in range(2):
            labels.append(int(pixel_str[4 * j:(j + 1) * 4], 2))

for i in range(len(labels)):
    labels[i] = classes[labels[i]]


print(classification_execution_time, loading_execution_time)

print(labels_holder)
print(sum(labels))

numpy.savetxt("labels.csv", labels, delimiter=",")
