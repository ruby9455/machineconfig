

iex (iwr "https://raw.githubusercontent.com/thisismygitrepo/machineconfig/main/src/machineconfig/setup_windows/uv.ps1").Content
function devops {
    & "$HOME\.local\bin\uv.exe" run --python 3.14 --with machineconfig devops $args
}

function cloud {
    & "$HOME\.local\bin\uv.exe" run --python 3.14 --with machineconfig cloud $args
}

function croshell {
    & "$HOME\.local\bin\uv.exe" run --python 3.14 --with machineconfig croshell $args
}

function agents {
    & "$HOME\.local\bin\uv.exe" run --python 3.14 --with machineconfig agents $args
}

function fire {
    & "$HOME\.local\bin\uv.exe" run --python 3.14 --with machineconfig fire $args
}

function ftpx {
    & "$HOME\.local\bin\uv.exe" run --python 3.14 --with machineconfig ftpx $args
}

function sessions {
    & "$HOME\.local\bin\uv.exe" run --python 3.14 --with machineconfig sessions $args
}

