#!/bin/bash


controller="./controllers/controller.py"
observe=1
rest=1

usage(){
	echo "usage: run-controller.h [[-f file]] [[-o]] [[-r]]"
}


while [ "$1" != "" ]; do
	case $1 in
		-f | --file ) shift
			      controller=$1
			      ;;
		-o | --observe-links )
				       observe=0
				       ;;
		-r | --rest ) 
			      rest=0
			      ;;
		* )	      usage
			      exit 1
	esac
	shift
done

if [ "$observe" == "1"  ] && [ "$rest" == "1"  ]; then
	ryu-manager $controller ryu.app.ofctl_rest --observe-links
elif [ "$observe" == "1" ]; then
	ryu-manager $controller --observe-links
elif [ "$rest" == "1" ]; then
	ryu-manager $controller ryu.ap.ofctl_rest
else
	ryu-manager $controller
fi
