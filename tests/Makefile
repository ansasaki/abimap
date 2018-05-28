DIRS= test_as_lib test_bump_version test_check test_check_files \
      test_clean_symbols test_get_info_from_release_string \
      test_get_version_from_string test_new test_overwrite_protected \
      test_script test_update

all: clean copy version
	@echo done

copy:
	@echo "Copying test data templates"
	cp -r data_template data;

version: $(DIRS)
	

%:
	@cd data/$@; \
	for i in * ; \
	do \
	sed -e 's/PROGRAM_NAME_VERSION/${SMAP_NAME_VERSION}/' -i $$i ; \
	done ;\
	cd ../..;

.PHONY: clean

clean:
	rm -rf data
