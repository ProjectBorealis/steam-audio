#
# Copyright 2017-2023 Valve Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import shutil
import urllib.request
import urllib.error
import urllib.parse
import zipfile
import argparse
import subprocess


version = "4.5.3"

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--configuration', help="Build configuration.",
                    choices=['debug', 'release'], type=str.lower, default='release')
parser.add_argument('-t', '--toolchain', help="Compiler toolchain. (Windows only)",
                    choices=['vs2013', 'vs2015', 'vs2017', 'vs2019', 'vs2022'], type=str.lower, default='vs2022')
parser.add_argument(
    '--all-platforms', help="Copy binaries for all available platforms.", action='store_true')
parser.add_argument(
    '--windows-x86', help="Copy binaries used for Windows x86.", action='store_true')
parser.add_argument(
    '--windows-x64', help="Copy binaries used for Windows x64.", action='store_true')
parser.add_argument(
    '--arm-v7a', help="Copy binaries used for android ARM v7a.", action='store_true')
parser.add_argument(
    '--arm-v8a', help="Copy binaries used for android ARM v8a.", action='store_true')
parser.add_argument(
    '--arm-x86', help="Copy binaries used for android x86.", action='store_true')
parser.add_argument(
    '--osx', help="Copy binaries used for osx.", action='store_true')
parser.add_argument(
    '--linux-x86', help="Copy binaries used for Linux x86.", action='store_true')
parser.add_argument(
    '--linux-x64', help="Copy binaries used for Linux x64.", action='store_true')
parser.add_argument(
    '--export', help="Export the plugin to specified UE plugins directory", default=None)
parser.add_argument('--version', help="Use specific version.", default=version)
parser.add_argument('--source', help="Build from source.", action='store_true')
args = parser.parse_args()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
lib_export_dir = "src/SteamAudioUnreal/Plugins/SteamAudio/Source/SteamAudioSDK/lib"

platforms = {"windows_x86": "windows-x86", "windows_x64": "windows-x64", "linux_x86": "linux-x86",
             "linux_x64": "linux-x64", "osx": "osx", "arm_v7a": "android/armeabi-v7a", "arm_v8a": "android/arm64-v8a", "arm_x86": "android/x86"}

platforms_to_use = set[str]()
if args.all_platforms:
    platforms_to_use = platforms.values
else:
    for key, platform in platforms.items():
        if args.__dict__[key]:
            platforms_to_use.add(platform)

print("Creating directories...")
for platform in platforms_to_use:
    os.makedirs(os.path.join(lib_export_dir, platform), exist_ok=True)

if args.source:
    command = ["python", "get_dependencies.py",
               "-t", args.toolchain, "--extra"]
    if args.configuration == "debug":
        command.append("--debug")
    ret = subprocess.call(command, cwd="../core/build")
    if ret != 0:
        print("Error getting dependencies!")
        exit(ret)

    print("\n Building...")
    command = ["python", "build.py", "-t",
               args.toolchain, "-c", args.configuration, "-o", "ci_build"]
    ret = subprocess.call(command, cwd="../core/build")
    if ret != 0:
        print("Error building steamaudio!")
        exit(ret)
    print("Build succeeded!")

    if "windows-x64" in platforms_to_use:
        shutil.copy("../core/build/windows-" + args.toolchain + "-x64/src/core/" + ("Release" if args.configuration == "release" else "Debug") + "/phonon.lib",
                    os.path.join(lib_export_dir, "windows-x64"))
        if os.path.exists("../core/deps/trueaudionext/bin/windows-x64/" + args.configuration + "/TrueAudioNext.dll"):
            shutil.copy("../core/deps/trueaudionext/bin/windows-x64/" + args.configuration + "/TrueAudioNext.dll",
                        os.path.join(lib_export_dir, "windows-x64"))
        if os.path.exists("../core/deps/trueaudionext/bin/windows-x64/" + args.configuration + "/GPUUtilities.dll"):
            shutil.copy("../core/deps/trueaudionext/bin/windows-x64/" + args.configuration + "/GPUUtilities.dll",
                        os.path.join(lib_export_dir, "windows-x64"))
        if os.path.exists("../core/deps/trueaudionext/lib/windows-x64/" + args.configuration + "/TrueAudioNext.lib"):
            shutil.copy("../core/deps/trueaudionext/lib/windows-x64/" + args.configuration + "/TrueAudioNext.lib",
                        os.path.join(lib_export_dir, "windows-x64"))
        if os.path.exists("../core/deps/trueaudionext/lib/windows-x64/" + args.configuration + "/GPUUtilities.lib"):
            shutil.copy("../core/deps/trueaudionext/lib/windows-x64/" + args.configuration + "/GPUUtilities.lib",
                        os.path.join(lib_export_dir, "windows-x64"))
        if args.configuration == "debug" and os.path.exists("../core/bin/symbols/windows-x64/phonon.pdb"):
            shutil.copy("../core/bin/symbols/windows-x64/phonon.pdb",
                        os.path.join(lib_export_dir, "windows-x64"))

    print("Copied steamaudio libraries to UE plugin source!")
else:
    def download_file(url):
        remote_file = urllib.request.urlopen(url)
        with open(os.path.basename(url), "wb") as local_file:
            while True:
                data = remote_file.read(1024)
                if not data:
                    break
                local_file.write(data)

    print("Downloading steamaudio_" + args.version + ".zip...")
    url = "https://github.com/ValveSoftware/steam-audio/releases/download/v" + \
        args.version + "/steamaudio_" + args.version + ".zip"
    download_file(url)

    print("Extracting steamaudio_" + args.version + ".zip...")
    with zipfile.ZipFile(os.path.basename(url), "r") as zip:
        zip.extractall()

    print("Copying files...")

    if "windows-x86" in platforms_to_use:
        shutil.copy("steamaudio/lib/windows-x86/phonon.dll",
                    os.path.join(lib_export_dir, "windows-x86"))
    if "windows-x64" in platforms_to_use:
        shutil.copy("steamaudio/lib/windows-x64/phonon.dll",
                    os.path.join(lib_export_dir, "windows-x64"))
        shutil.copy("steamaudio/lib/windows-x64/TrueAudioNext.dll",
                    os.path.join(lib_export_dir, "windows-x64"))
        shutil.copy("steamaudio/lib/windows-x64/GPUUtilities.dll",
                    os.path.join(lib_export_dir, "windows-x64"))
    if "linux-x86" in platforms_to_use:
        shutil.copy("steamaudio/lib/linux-x86/libphonon.so",
                    os.path.join(lib_export_dir, "linux-x86"))
    if "linux-x64" in platforms_to_use:
        shutil.copy("steamaudio/lib/linux-x64/libphonon.so",
                    os.path.join(lib_export_dir, "linux-x64"))
    if "android/armeabi-v7a" in platforms_to_use:
        shutil.copy("steamaudio/lib/android-armv7/libphonon.so",
                    os.path.join(lib_export_dir, "android/armeabi-v7a"))
    if "android/armeabi-v8a" in platforms_to_use:
        shutil.copy("steamaudio/lib/android-armv8/libphonon.so",
                    os.path.join(lib_export_dir, "android/armeabi-v8a"))
    if "android/x86" in platforms_to_use:
        shutil.copy("steamaudio/lib/android-x86/libphonon.so",
                    os.path.join(lib_export_dir, "android/x86"))

    if "osx" in platforms_to_use:
        osx_phonon_dest = os.path.join(lib_export_dir, "osx", "phonon.bundle")
        if os.path.exists(osx_phonon_dest):
            shutil.rmtree(osx_phonon_dest)
        shutil.copytree("steamaudio/lib/osx/phonon.bundle", osx_phonon_dest)

    print("Cleaning up...")
    shutil.rmtree("steamaudio")

if args.export and os.path.exists(args.export):
    print("\nExporting plugins to " + args.export + "...")
    plugins_local_dir = "src/SteamAudioUnreal/Plugins"
    for plugin in os.listdir(plugins_local_dir):
        target_dir = os.path.join(args.export, plugin)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(os.path.join(plugins_local_dir, plugin), target_dir)
        os.remove(os.path.join(target_dir, plugin + ".uplugin.in"))
    print("Done!")
