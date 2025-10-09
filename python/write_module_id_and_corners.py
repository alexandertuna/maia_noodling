import argparse
from array import array
import os
from typing import TextIO

import ROOT
TGEOMANAGER_NAME = "default"

def options():
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", type=str, default="MAIA_LST_v0.root",
                        help="Path to the input root geometry file")
    parser.add_argument("-o", type=str, default="MAIA_LST_v0.modules.txt",
                        help="Path to the output text file")
    return parser.parse_args()

def main():
    args = options()
    if not os.path.isfile(args.i):
        raise Exception(f"Input file not found: {args.i}")

    with open(args.o, "w") as output:
        write_module_id_and_corners(args.i, output)

def write_module_id_and_corners(fname: str, output: TextIO) -> None:
    fi = ROOT.TFile.Open(fname)
    geo = fi.Get(TGEOMANAGER_NAME)

    IT = "InnerTracker"
    OT = "OuterTracker"
    TRACKERS = [IT, OT]
    ITB = "InnerTrackerBarrel_assembly"
    OTB = "OuterTrackerBarrel_assembly"
    SENSOR = "sensor"

    world_volume = geo.GetTopNode()
    print("World volume:", world_volume.GetName())

    detectors = world_volume.GetNdaughters()
    for i_detector in range(detectors):
        detector = world_volume.GetDaughter(i_detector)
        print(f"Detector {i_detector}/{detectors-1}: {detector.GetName()}")
        if not any(trk in detector.GetName() for trk in TRACKERS):
            continue

        assemblies = detector.GetNdaughters()
        for i_assembly in range(assemblies):
            assembly = detector.GetDaughter(i_assembly)
            assembly_name = assembly.GetName()
            print(f" Assembly {i_assembly}/{assemblies-1}: {assembly_name}")
            if not any(assem in assembly_name for assem in [ITB, OTB]):
                continue

            layers = assembly.GetNdaughters()
            for i_layer in range(layers):
                # if i_layer > 1:
                #     break
                layer = assembly.GetDaughter(i_layer)
                layer_name = layer.GetName()
                print(f"  Layer {i_layer}/{layers-1}: {layer_name}")

                modules = layer.GetNdaughters()
                for i_module in range(modules):
                    # if i_module > 1:
                    #     break
                    module = layer.GetDaughter(i_module)
                    # print(f"   Module {i_module}/{modules-1}: {module.GetName()}")
                    module_name = module.GetName()
                    module_id = int(module_name.split("_")[-1])
                    if i_module != module_id:
                        raise Exception(f"Module id mismatch: {i_module} vs {module_id}")

                    vol = module.GetVolume()
                    shape = vol.GetShape()
                    # print("Here:", module.GetName(), " volume:", vol.GetName(), " shape:", shape.ClassName())
                    if shape.ClassName() != "TGeoBBox":
                        raise Exception(f"Unexpected shape class: {shape.ClassName()} in {module.GetName()}")

                    # get local corners
                    dx, dy = shape.GetDX(), shape.GetDY()
                    local_corners = [
                        array("d", [ dx,  dy, 0]),
                        array("d", [ dx, -dy, 0]),
                        array("d", [-dx,  dy, 0]),
                        array("d", [-dx, -dy, 0]),
                    ]

                    # get global corners
                    global_corners = []
                    for local in local_corners:
                        globl = array("d", [0.0, 0.0, 0.0])
                        module.LocalToMaster(local, globl)
                        global_corners.append(globl)

                    # write to output
                    line = f"{assembly_name} {layer_name} {module_id:>6}"
                    for (gx, gy, gz) in global_corners:
                        line += f" {gx:10.5f} {gy:10.5f} {gz:10.5f}"
                    output.write(line + "\n")


                    # sensors = module.GetNdaughters()
                    # for i_sensor in range(sensors):
                    #     sensor = module.GetDaughter(i_sensor)
                    #     if SENSOR not in sensor.GetName():
                    #         continue
                        # print(f"    Sensor {i_sensor}/{sensors-1}: {sensor.GetName()}")

                        # vol = sensor.GetVolume()
                        # shape = vol.GetShape()
                        # # print("Here:", sensor.GetName(), " volume:", vol.GetName(), " shape:", shape.ClassName())
                        # if shape.ClassName() != "TGeoBBox":
                        #     raise Exception(f"Unexpected shape class: {shape.ClassName()} in {sensor.GetName()}")
                        # dx, dy, dz = shape.GetDX(), shape.GetDY(), shape.GetDZ()
                        # local_corners = [
                        #     array("d", [ dx,  dy, 0]),
                        #     array("d", [ dx, -dy, 0]),
                        #     array("d", [-dx,  dy, 0]),
                        #     array("d", [-dx, -dy, 0]),
                        # ]

                        # # get global corners
                        # line = f"{assembly_name} {layer_name} {module_id}"
                        # for local in local_corners:
                        #     globl = array("d", [0.0, 0.0, 0.0])
                        #     sensor.LocalToMaster(local, globl)
                        #     line += f" {globl[0]:.6f} {globl[1]:.6f} {globl[2]:.6f}"
                        # output.write(line + "\n")


                    # vol = module.GetVolume()
                    # shape = vol.GetShape()
                    # print("    Shape class:", shape.ClassName())  # often TGeoBBox
                    # dx, dy, dz = shape.GetDX(), shape.GetDY(), shape.GetDZ()
                    # local = array("d", [0.0, 0.0, 0.0])
                    # globl = array("d", [0.0, 0.0, 0.0])
                    # geo.LocalToMaster(local, globl)
                    # print("    Half dimensions (dx, dy, dz):", dx, dy, dz)
                    # print("    Global center (x, y, z):", globl[0], globl[1], globl[2])


def old():

    sensor_path = "world_volume_1/OuterTrackers_9/OuterTrackerBarrel_assembly_0"
    ok = geo.cd(sensor_path)
    if not ok:
        raise Exception(f"Failed to cd to {sensor_path}")
    node = geo.GetCurrentNode()
    print("Here:", node.GetName())
    for i_layer in range(node.GetNdaughters()):
        if i_layer > 2:
            break
        layer = node.GetDaughter(i_layer)
        print(f" Layer {i_layer}/{node.GetNdaughters()-1}: {layer.GetName()}")
        for i_module in range(layer.GetNdaughters()):
            module = layer.GetDaughter(i_module)
            print(f"  Module {i_module}/{layer.GetNdaughters()-1}: {module.GetName()}")
            if i_module > 2:
                break
        
            # vol = module.GetVolume()
            # shape = vol.GetShape()
            # print("  Shape class:", shape.ClassName())  # often TGeoBBox
            # dx, dy, dz = shape.GetDX(), shape.GetDY(), shape.GetDZ()
            # local = array("d", [0.0, 0.0, 0.0])
            # globl = array("d", [0.0, 0.0, 0.0])
            # geo.LocalToMaster(local, globl)
            # print("  Half dimensions (dx, dy, dz):", dx, dy, dz)
            # print("  Global center (x, y, z):", globl[0], globl[1], globl[2])

def xxxx(fname: str):
    fi = ROOT.TFile.Open(fname)
    geo = fi.Get(TGEOMANAGER_NAME)
    sensor_path = "world_volume_1/OuterTrackers_9/OuterTrackerBarrel_assembly_0/layer0_0/OuterTrackerBarrelModule_In_2/sensor8_8"
    ok = geo.cd(sensor_path)
    if not ok:
        raise Exception(f"Failed to cd to {sensor_path}")
    node = geo.GetCurrentNode()
    vol = node.GetVolume()
    print("Here:", node.GetName(), " volume:", vol.GetName())
    shape = vol.GetShape()
    print("Shape class:", shape.ClassName())  # often TGeoBBox
    dx, dy, dz = shape.GetDX(), shape.GetDY(), shape.GetDZ()
    local = array("d", [0.0, 0.0, 0.0])
    globl = array("d", [0.0, 0.0, 0.0])
    geo.LocalToMaster(local, globl)
    print("Half dimensions (dx, dy, dz):", dx, dy, dz)
    print("Global center (x, y, z):", globl[0], globl[1], globl[2])


def main2():
    fi = ROOT.TFile.Open(args.i)
    geo = fi.Get(TGEOMANAGER_NAME)
    sensor_path = "world_volume_1/OuterTrackers_9/OuterTrackerBarrel_assembly_0/layer0_0/OuterTrackerBarrelModule_In_2/sensor8_8"
    vol = geo.GetVolume(sensor_path)  # if you know the exact volume name
    print(vol)


if __name__ == "__main__":
    main()
