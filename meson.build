project('UniversalDevManager',
    version: '1.0.3',
    meson_version: '>= 1.0.0',
    default_options: ['warning_level=1'],
)

python = find_program('python3', 'python')

scripts_dir = meson.project_source_root() / 'scripts'

run_target('build-exe',
    command: [python, scripts_dir / 'build_exe.py'],
)

run_target('build-appimage',
    command: ['bash', scripts_dir / 'build_appimage.sh'],
)

run_target('build-dmg',
    command: ['bash', scripts_dir / 'build_dmg.sh'],
)
