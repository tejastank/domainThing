
git:
  pkg.installed:
    - name: git

git_domainThing:
  git.latest:
    - name: https://github.com/allmightyspiff/domainThing.git
    - target: /domainThing
    - require:
      - pkg: git



domainThing_conf:
  file.managed:
    - name: '/domainThing/config.cfg'
    - template: jinja
    - source: salt://domainThing/config-template.cfg
    - require:
      - git: git_domainThing
    - mode: 644


