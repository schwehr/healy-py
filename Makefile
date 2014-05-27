VERSION := ${shell cat VERSION}

default:
	@echo "    === Healy KML / Google Earth Visualization ==="
	@echo "         A joint USCG, LDGO, CCOM/JHC project"
	@echo "  update - reprocess everything and upload to the server"

update-aloftcon:
	./aloftcon2kml.py
	scp HEADER.html healy-aloftcon-latest.kml healy-aloftcon-latest.georss vislab-ccom:www/healy/
	rsync --recursive --perms --times --cvs-exclude --verbose *small*.jpg vislab-ccom:www/healy/small/
	-rm 201[0-9]*small.jpg
	-rm 201[0-9]*.jpeg

update-science:
	rm -f healy.db3
	scp mail.ccom.unh.edu:mail/healy .
	PATH=/sw/bin ./healy_email_data.py > /dev/null
	PATH=/sw/bin ./healy_sqlite2feeds.py
	scp healy-science-*.atom healy-science-*.rss healy-science-{latest,updating}.kml vislab-ccom:www/healy/

TAR_DIR:=healy-py-${VERSION}
tar:
	rm -rf ${TAR_DIR}
	mkdir ${TAR_DIR}
	cp LICENSE.txt Makefile README.txt *.py HEADER.html.tmpl healy64x64.png ${TAR_DIR}/
	tar cf ${TAR_DIR}{.tar,}
	rm -rf ${TAR_DIR} ${TAR_DIR}.tar.bz2
	bzip2 -9 ${TAR_DIR}.tar

release:
	scp ${TAR_DIR}.tar.bz2 vislab-ccom:www/software/healy-py/

clean:
	-rm -f 201[0-9]*.jpeg healy-aloftcon-latest.kml
	-rm -f 201[0-9]*small.jpg
	-rm -f *.georss healy-aloftcon-latest.kml HEADER.html
	-rm -rf *.tar* healy-py-[0-9].[0-9]*

.PHONY:
email:
	@echo "Only works at Kurt"
	scp mail.ccom.unh.edu:mail/healy .

science-report: email
	rm -f healy.db3; ./healy_email_data.py -v
	./healy_sqlite2kml.py -v

test:
	rm -f healy.db3; ./healy_email_data.py -v

