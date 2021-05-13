import os
import shutil


def dem_files(path) -> os.DirEntry:
    """ yield up al lthe .dem files """
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from dem_files(entry.path)
        elif entry.path.endswith('elevation.tif'):

            yield entry


def main():
    dem_dir = '/home/sybrand/Downloads/Work/topo/mtec'
    target_dir = '/home/sybrand/Work/topo_tiff'
    for dem_entry in dem_files(dem_dir):
        print(f'copy {dem_entry.name}')
        shutil.copyfile(dem_entry.path, f'{os.path.join(target_dir, dem_entry.name)}')


if __name__ == '__main__':
    main()
