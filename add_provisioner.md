```bash

- name: Check the Python version
      command: "{{ ansible_python_interpreter | default('/usr/bin/python3') }} --version"
      register: python_version

    - debug:
        msg: "Python version: {{ python_version.stdout }}"

    - name: Ensure jmespath is installed with Python 3
      pip:
        name: jmespath
        state: present
        executable: "{{ ansible_python_interpreter | default('/usr/bin/python3') }}"
      when: python_version.stdout is search('Python 3')

    - name: Ensure jmespath is installed with Python 2
      pip:
        name: jmespath
        state: present
        executable: "{{ ansible_python_interpreter | default('/usr/bin/python') }}"
      when: python_version.stdout is search('Python 2')
```
