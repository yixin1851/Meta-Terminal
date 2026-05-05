/** @brief      The type definition file
                
    @file       TypeDefine.h
    @author     KONICA MINOLTA, INC.

	Copyright(c) 2013-2016 KONICA MINOLTA, INC. All rights reserved.
*/

#ifndef __TYPEDEFINE_H__
#define __TYPEDEFINE_H__

#if defined(_WIN32) || defined(_WIN64)
	#include <windows.h>		//!< The define for Windows OS (WORD,DWORD etc.)
	#define KMAPI __stdcall		//!< stdcall (for Windows OS)
#elif defined(__APPLE__)
	#include <wchar.h>
	#define KMAPI				//!< _cdecl (for OS except Windows OS)
	#define TRUE 1
	#define FALSE 0
#else
	#define KMAPI				//!< _cdecl (for OS except Windows OS)
	#define TRUE 1
	#define FALSE 0
#endif

#if defined(_WIN32)
	/* For Windows OS [32bit] */
	typedef	char				int8_km;			//!< 8bit (signed)
	typedef	unsigned char		uint8_km;			//!< 8bit (unsigned)
	typedef	short				int16_km;			//!< 16bit(signed)
	typedef	unsigned short		uint16_km;			//!< 16bit(unsigned)
	typedef	int					int32_km;			//!< 32bit(signed)
	typedef	unsigned int		uint32_km;			//!< 32bit(unsigned)
	typedef	long long			int64_km;			//!< 64bit(signed)
	typedef	unsigned long long	uint64_km;			//!< 64bit(unsigned)
	typedef void* DEVICE_HANDLE;
	typedef float real;

#elif defined(_WIN64)
	/* For Windows OS [64bit] */
	typedef	char				int8_km;			//!< 8bit (signed)
	typedef	unsigned char		uint8_km;			//!< 8bit (unsigned)
	typedef	short				int16_km;			//!< 16bit(signed)
	typedef	unsigned short		uint16_km;			//!< 16bit(unsigned)
	typedef	int					int32_km;			//!< 32bit(signed)
	typedef	unsigned int		uint32_km;			//!< 32bit(unsigned)
	typedef	long long			int64_km;			//!< 64bit(signed)
	typedef	unsigned long long	uint64_km;			//!< 64bit(unsigned)
	typedef void* DEVICE_HANDLE;
	typedef float real;

#elif defined(__APPLE__)
	/* For MacOS [64bit] */
	typedef	char				int8_km;			//!< 8bit (signed)
	typedef	unsigned char		uint8_km;			//!< 8bit (unsigned)
	typedef	short				int16_km;			//!< 16bit(signed)
	typedef	unsigned short		uint16_km;			//!< 16bit(unsigned)
	typedef	int					int32_km;			//!< 32bit(signed)
	typedef	unsigned int		uint32_km;			//!< 32bit(unsigned)
	typedef	long long			int64_km;			//!< 64bit(signed)
	typedef	unsigned long long	uint64_km;			//!< 64bit(unsigned)
	typedef uint8_km BYTE;
	typedef uint16_km WORD;
	typedef uint32_km DWORD;
	typedef void* DEVICE_HANDLE;
	typedef float real;

#else
	/* For Firmware */
	typedef	char				int8_km;			//!< 8bit (signed)
	typedef	unsigned char		uint8_km;			//!< 8bit (unsigned)
	typedef	short				int16_km;			//!< 16bit(signed)
	typedef	unsigned short		uint16_km;			//!< 16bit(unsigned)
	typedef	int					int32_km;			//!< 32bit(signed)
	typedef	unsigned long		uint32_km;			//!< 32bit(unsigned)
	typedef	long long			int64_km;			//!< 64bit(signed)
	typedef	unsigned long long	uint64_km;			//!< 64bit(unsigned)
	typedef uint16_km wchar_t;
	typedef uint8_km BYTE;
	typedef uint16_km WORD;
	typedef uint32_km DWORD;
	typedef void* DEVICE_HANDLE;
	typedef float real;
#endif

#endif /*__TYPEDEFINE_H__*/
