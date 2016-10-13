# Prerequisites
- STM32CubeMX
- python
- python-lxml

# Flow
1. Parse .ioc file as a  dictionary 
2. Find MCU part number in the dictionary
2. Open db/mcu/families.xml and find the file were we can find the file where the information about the MCU is located
3. Open the MCU xml description file
4. Load the MCU information: GPIO for the moment
5. Update MCU properties from the dictionary
6. Mix the information with the existing chibi config file if provided
7. Save chibi config file
