def _handle_GDAL_depencies():
    import os
    import glob
    from win32api import GetFileVersionInfo, LOWORD, HIWORD

    gdal_installations = []
    if "PATH" in os.environ:
        for p in os.environ["PATH"].split(os.pathsep):
            if p and glob.glob(os.path.join(p, "gdal*.dll")):
                gdal_installations.append(os.path.abspath(p))

    if len(gdal_installations) > 1:
        for folder in gdal_installations:
            filenames = [
                f
                for f in os.listdir(folder)
                if f.startswith("gdal") & f.endswith(".dll")
            ]

            for filename in filenames:
                filename = os.path.join(folder, filename)

                if not os.path.exists(filename):
                    print("no gdal dlls found in " + folder)
                    os.environ["PATH"] = os.pathsep.join(
                        [
                            p
                            for p in os.environ["PATH"].split(os.pathsep)
                            if folder not in p
                        ]
                    )
                    continue
                try:
                    info = GetFileVersionInfo(filename, "\\")
                except:
                    continue

                major_version = HIWORD(info["FileVersionMS"])
                minor_version = LOWORD(info["FileVersionMS"])

                if (major_version < 3) | (minor_version < 6):
                    os.environ["PATH"] = os.pathsep.join(
                        [
                            p
                            for p in os.environ["PATH"].split(os.pathsep)
                            if folder not in p
                        ]
                    )
    return
