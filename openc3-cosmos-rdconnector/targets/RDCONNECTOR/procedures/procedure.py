# Script Runner test script
cmd("RDCONNECTOR EXAMPLE")
wait_check("RDCONNECTOR STATUS BOOL == 'FALSE'", 5)
