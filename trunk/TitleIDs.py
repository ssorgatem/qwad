#-*- coding: utf-8 -*-
"""
module storing a titleid dictionary
"""
import binascii

IDdict = {
"BOOT2":"0000000100000001",
"System Menu":"0000000100000002",
"BC":"0000000100000100",
"MIOS":"0000000100000101",
"IOS4":"0000000100000004",
"IOS9":"0000000100000009",
"IOS10":"000000010000000a",
"IOS11":"000000010000000b",
"IOS12":"000000010000000c",
"IOS13":"000000010000000d",
"IOS14":"000000010000000e",
"IOS15":"000000010000000f",
"IOS16":"0000000100000010",
"IOS17":"0000000100000011",
"IOS20":"0000000100000014",
"IOS21":"0000000100000015",
"IOS22":"0000000100000016",
"IOS28":"000000010000001c",
"IOS30":"000000010000001e",
"IOS31":"000000010000001f",
"IOS33":"0000000100000021",
"IOS34":"0000000100000022",
"IOS35":"0000000100000023",
"IOS36":"0000000100000024",
"IOS37":"0000000100000025",
#TODO: Add remaining IOSes
"Wii Speak Channel":"00010001484346xx",
"Photo Channel 1.1 (Europe?)":"0001000148415axx",
"Metroid Prime 3 Preview":"00010001484157xx",
"Nintendo Channel":"00010001484154xx",
"Check Mii Out / Mii Contest Channel":"00010001484150xx",
"Everyone Votes Channel":"0001000148414axx",
"Opera / Internet Channel":"00010001484144xx",
"Photo Channel":"00010002-48414141",
"Shopping Channel":"0010002-48414241",
"Mii Channel":"001000248414341",
"Photo Channel 1.1":"001000248415941",
"Wii Message Board":"001000148414541",
"Weather Channel-HAFx":"00010002484146xx",
"Weather Channel-HAFA":"0001000248414641",
"News Channel-HAGx":"00010002484147xx",
"News Channel-HAGA":"0001000248414741"}

def AsciiID(channelname):
    return binascii.unhexlify(IDdict[channelname][7:])

if __name__ == "__main__":
    print IDdict
    print IDdict["BOOT2"]
    print IDdict["Mii Channel"][7:]
    print AsciiID("Mii Channel")
