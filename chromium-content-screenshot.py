#!/usr/bin/env python

# chromium-content-screenshot.py [input_file] [output_file]
# Reads [input_file] as it would be renderered by chromium and writes the
# resulting png to [output_file].

import subprocess
import argparse
import platform
import subprocess
import os
import urllib
import base64

def prebuiltContentShellBinary(system, rev, binary):
    binaryRoot = os.path.dirname(os.path.abspath(__file__)) + "/binaries/" + rev + "." + system
    binaryPath = binaryRoot + "/" + binary
    zipPath = binaryRoot + ".zip"
    if (not os.path.exists(binaryPath)):
        if (os.path.exists(zipPath)):
            subprocess.call(["unzip", zipPath, "-d", binaryRoot], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (not os.path.exists(binaryPath)):
        raise Exception("A prebuilt content shell binary was not found for your platform. If you have a chromium checkout, you may specify your own content shell binary using --content-shell")
    return binaryPath

def contentShellBinary(contentShell):
    if (contentShell and os.path.exists(contentShell)):
        return contentShell
    system = platform.system()
    if (system == "Darwin"):
        return prebuiltContentShellBinary("mac", "72cff265974701c8e6453e8b47a91d03053ea140", "Content Shell.app/Contents/MacOS/Content Shell")
    elif (system == "Linux"):
        if (platform.architecture()[0] == "64bit"):
            return prebuiltContentShellBinary("linux64", "72cff265974701c8e6453e8b47a91d03053ea140", "content_shell")
    #elif (system == "Windows"):
    #    TODO: Build this.
    raise Exception("A prebuilt content shell binary was not found for your platform. If you have a chromium checkout, you may specify your own content shell binary using --content-shell")

def dumpSvgAsBase64PngUrl(input, width, height):
    dumpSvgPng = "dump-svg-as-base64-png.html"
    dumpSvgPngPath = os.path.dirname(os.path.abspath(__file__)) + "/" + dumpSvgPng
    if (not os.path.exists(dumpSvgPngPath)):
        raise Exception(dumpSvgPngPath + " was not found")
    if (os.path.exists(input)):
        input = "file://" + os.getcwd() + "/" + input
    size = ""
    if (width):
        size = size + "width=" + str(width)
    if (height):
        if (len(size) > 0):
            size = size + "&"
        size = size + "height=" + str(height)
    url = ""
    if (len(size) > 0):
        url = "&"
    url = url + "url=" + urllib.quote(input)
    return "file://" + dumpSvgPngPath + "?" + size + url

def extractImage(output, svgMode):
    if (svgMode):
        SVG_PNG_START = "SvgPngBase64Encoded->"
        SVG_PNG_END = "<-SvgPngBase64Encoded"
        try:
            start = output.index(SVG_PNG_START) + len(SVG_PNG_START)
            end = output.index(SVG_PNG_END)
            base64Data = output[start:end]
            return base64.decodestring(base64Data)
        except ValueError:
            raise Exception("Content shell did not output a valid svg png")
    PNG_START = b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
    PNG_END = b"\x49\x45\x4E\x44\xAE\x42\x60\x82"
    try:
        start = output.index(PNG_START)
        end = output.rindex(PNG_END) + 8
    except ValueError:
        raise Exception("Content shell did not output a valid png")
    return output[start:end]

def dumpPng(contentShell, input, output, flags, width, height, svgMode):
    if (svgMode):
        input = dumpSvgAsBase64PngUrl(input, width, height)
    else:
        # Use a special flag for controlling the window size.
        SIZE_FLAG = "content-shell-host-window-size"
        width = args.width if args.width else 800
        height = args.height if args.height else 600
        if (SIZE_FLAG not in flags):
            flags = flags + " --" + SIZE_FLAG + "=" + str(width) + "x" + str(height)

        # Pixel results are enabled with the pixel-test "flag" after the input.
        # The single quote is a separator (see: layout_test_browser_main.cc).
        input = input + "'--pixel-test"

    p = subprocess.Popen([contentShell,
                          "--run-layout-test",
                          "--enable-font-antialiasing",
                          flags,
                          input
                         ],
                         shell = False,
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE)
    result = p.stdout.read()

    image = extractImage(result, svgMode)
    with open(output, "wb") as outputFile:
        outputFile.write(image)
        print "Done"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="chromium-content-screenshot: command line tool for converting html/svg to png")
    parser.add_argument("input", help="input (html file, svg file, or url")
    parser.add_argument("output", help="output png result file")
    parser.add_argument("--content-shell", dest="contentShell", help="content shell binary")
    parser.add_argument("--flags", help="additional flags to pass to content shell")
    parser.add_argument("--width", help="width of rendering (px)", type=int)
    parser.add_argument("--height", help="height of rendering (px)", type=int)
    parser.add_argument("--no-svg-mode", dest="noSvgMode", help="disable special handling of SVG files")
    args = parser.parse_args()

    flags = args.flags if args.flags else ""
    svgMode = args.input.endswith("svg") and not args.noSvgMode
    binary = contentShellBinary(args.contentShell)
    dumpPng(binary, args.input, args.output, flags, args.width, args.height, svgMode)