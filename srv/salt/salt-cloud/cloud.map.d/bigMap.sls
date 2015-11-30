{% for name,location in salt["pillar.get"]("cloud-profiles:datacenters", {}).items() %}
{{ name }}:
  {% for number in range(location.number) %}
  - minion-{{ number }}:
      minion:
        mine_functions:
          network.ip_addrs:
            interface: eth0
        grains:
          roles: resolver
  {% endfor %}
{% endfor %}


dal09:
  - minion-consumer:
      minion:
        mine_functions:
          network.ip_addrs:
            interface: eth0
        grains:
          roles: consumer
  - minion-parser:
      minion:
        mine_functions:
          network.ip_addrs:
            interface: eth0
        grains:
          roles: parser
