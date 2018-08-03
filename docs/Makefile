
all: usage readme

HELP:
	echo 'Running  ``$ abimap -h`` will give::' > HELP
	echo >> HELP
	abimap -h | sed -e 's/^/  /' >> HELP

HELP_NEW:
	echo 'Running ``$ abimap new -h`` will give::' > HELP_NEW
	echo >> HELP_NEW
	abimap new -h | sed -e 's/^/  /' >> HELP_NEW

HELP_UPDATE:
	echo 'Running ``$ abimap update -h`` will give::' > HELP_UPDATE
	echo >> HELP_UPDATE
	abimap update -h | sed -e 's/^/  /' >> HELP_UPDATE

HELP_CHECK:
	echo 'Running ``$ abimap check -h`` will give::' > HELP_CHECK
	echo >> HELP_CHECK
	abimap check -h | sed -e 's/^/  /' >> HELP_CHECK

HELP_VERSION:
	echo 'Running ``$ abimap version -h`` will give::' > HELP_VERSION
	echo >> HELP_VERSION
	abimap version -h | sed -e 's/^/  /' >> HELP_VERSION

usage: HELP HELP_NEW HELP_UPDATE HELP_CHECK HELP_VERSION
	cp templates/usage.template usage.rst
	sed -e '/HELP_PLACEHOLDER/ {' -e 'r HELP' -e 'd' -e '}' -i usage.rst
	sed -e '/HELP_UPDATE_PLACEHOLDER/ {' -e 'r HELP_UPDATE' -e 'd' -e '}' -i usage.rst
	sed -e '/HELP_NEW_PLACEHOLDER/ {' -e 'r HELP_NEW' -e 'd' -e '}' -i usage.rst
	sed -e '/HELP_CHECK_PLACEHOLDER/ {' -e 'r HELP_CHECK' -e 'd' -e '}' -i usage.rst
	sed -e '/HELP_VERSION_PLACEHOLDER/ {' -e 'r HELP_VERSION' -e 'd' -e '}' -i usage.rst

readme: HELP HELP_NEW HELP_UPDATE HELP_CHECK HELP_VERSION
	cp templates/readme.template readme.rst
	sed -e '/HELP_PLACEHOLDER/ {' -e 'r HELP' -e 'd' -e '}' -i readme.rst
	sed -e '/HELP_UPDATE_PLACEHOLDER/ {' -e 'r HELP_UPDATE' -e 'd' -e '}' -i readme.rst
	sed -e '/HELP_NEW_PLACEHOLDER/ {' -e 'r HELP_NEW' -e 'd' -e '}' -i readme.rst
	sed -e '/HELP_CHECK_PLACEHOLDER/ {' -e 'r HELP_CHECK' -e 'd' -e '}' -i readme.rst
	sed -e '/HELP_VERSION_PLACEHOLDER/ {' -e 'r HELP_VERSION' -e 'd' -e '}' -i readme.rst

.PHONY: clean

clean:
	rm -rf HELP HELP_NEW HELP_UPDATE HELP_CHECK HELP_VERSION

