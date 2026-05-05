/** @brief      The definition file of the version information
                
    @file       Version.h
    @author     KONICA MINOLTA, INC.

	Copyright(c) 2012-2016 KONICA MINOLTA, INC. All rights reserved.
*/


#ifndef _EIGER_VERSION_H_
#define _EIGER_VERSION_H_

#if defined(_WIN32) || defined(__APPLE__)
#pragma pack(push,4) 
#endif

#include "TypeDefine.h"

/*!
 * common version structure
 * @brief common version structure 
 * @attention the invalid number is 0.00.0000
 */
typedef struct tVERSION
{
	uint32_km Major;	//!< the major version number (2-digit)
	uint32_km Minor;	//!< the minor version number (2-digit)
	uint32_km Free;		//!< the reserve version number (4-digit) 
} VERSION;

/*!
 * The structure of version information on the CL-SDK
 * @brief The information on version of the CL-SDK
 */
typedef struct tCL_SDK_VERSION{
	VERSION Main;		//!< Version information of the interface library
	VERSION Calib;		//!< Version information of the calibration library
	VERSION Com;		//!< Version information of the device communication library
	VERSION Color;		//!< Version information of the color calculating library
}
CL_SDKVERSION;


/*!
 * type of programs of the body
 * @brief type of the firmware
 */
typedef enum tPRG_FIRM_TYPES
{
	PRG_FIRM_MAIN,		//!< the main program of the body
	PRG_FIRM_BOOT,		//!< the boot program of the bopy
	PRG_FIRM_SUB,		//!< the sub-program of the body
	PRG_FIRM_PLD,		//!< the sub-program of the body
	RPG_FIRM_NO,		//!< the number of programs of the body
}PRG_FIRM_TYPES;


//!< FIRMWARE versions
typedef VERSION FIRMVERSIONS[RPG_FIRM_NO];


#if defined(_WIN32) || defined(__APPLE__)
#pragma pack(pop) 
#endif

#endif
