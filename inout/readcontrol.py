def readControl(path):
    file = open(path, "r")
    lines = file.readlines()
    file.close()
    output = {}
    for line in lines:
        line = line.strip(" \n")
        if line == "" or line.startswith("$"): continue
        line = line.split("=")
        line[0] = line[0].strip(" ")
        line[1] = line[1].strip(" ")
        if line[1] == "T":
            output[line[0]] = True
        elif line[1] == "F":
            output[line[0]] = False
        elif line[1].isdigit():
            print(line[0])
            output[line[0]] = int(line[1])
        elif line[1].replace(".", "", 1).isdigit():
            output[line[0]] = float(line[1])
        elif line[1].startswith("'") and line[1].endswith("'"):
            output[line[0]] = line[1].strip("'")
        else:
            output[line[0]] = line[1]
    return output