sjc01:
  - minion-00:
      minion:
        mine_functions:
          network.ip_addrs:
            interface: eth0
        grains:
          roles: resolver
