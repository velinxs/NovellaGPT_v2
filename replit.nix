{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.python310Packages.virtualenv
    pkgs.python310Packages.pydub
    pkgs.ffmpeg
  ];
}