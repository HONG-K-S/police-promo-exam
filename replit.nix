{ pkgs }: {
  deps = [
    pkgs.python39
    pkgs.python39Packages.flask
    pkgs.python39Packages.flask-sqlalchemy
    pkgs.python39Packages.python-dotenv
  ];
} 