/** @brief      The definition file of the information in using the CL-SDK
                
    @file       CLConditions.h
    @author     KONICA MINOLTA, INC.

	Copyright(c) 2012-2016 KONICA MINOLTA, INC. All rights reserved.
*/

#ifndef _CL_CONDITIONS_H_
#define _CL_CONDITIONS_H_

#include "CLColorConditions.h"
#include "Version.h"

#if defined(_WIN32) || defined(__APPLE__)
#pragma pack(push,4)
#endif

//===========================
// TypeDefine
//===========================
typedef int8_km CL_PRODUCT_CODE; //!< product code
typedef int8_km CL_FACTORY_CODE; //!< factory code
typedef uint32_km CL_SERIAL_CODE; //!< serial number
typedef uint32_km CL_VARIATION_CODE; //!< variation code

//===========================
// The definition value
//===========================
// User Calibration
#define CL_USERCALIB_NAMESIZE 13		//!< The maximum character length of user calibration data name (including NULL character)

#define CL_USERCALIB_CH_DISABLE 0		//!<
#define CL_USERCALIB_CH_ALLDEL -1		//!< The value for deleting the all user calibration coefficient in the instrument
#define CL_USERCALIB_CH_START 1			//!< The start No. which is available when specifying the user calibration coefficient
#define CL_USERCALIB_CH_END 10			//!< The last No. which is available when specifying the user calibration coefficient

// Target Data
#define CL_TARGET_NAMESIZE 13			//!< The maximum character length of target data name (including NULL character)
#define CL_TARGET_NO_ALLDEL -1			//!< The value for deleting the all target data in the instrument
#define CL_TARGET_NO_START 1			//!< The start No. which is available when specifying the target data
#define CL_TARGET_NO_END 20				//!< The last No. which is available when specifying the target data

// RANK
#define CL_RANK_POINTNUM 10				//!< The maximum point number which can configure as rank area
#define CL_RANK_NAMESIZE 16				//!<
#define CL_RANK_NAMESIZE_SAVE 41		//!< The maximum byte size of rank data name (including NULL character)
#define CL_RANK_NO_ALLDEL -1			//!< The value for deleting the all rank data in the instrument
#define CL_RANK_NO_START 1				//!< The start No. which can specify on the rank data
#define CL_RANK_NO_END 20				//!< The end No. which can specify on the rank data

// Stored Data
#define CL_LIST_NO_ALLDEL -1			//!< The value for deleting the all stored data in the instrument
#define CL_LIST_NO_START 1				//!< The start No. which can specify on the stored data in the instrument
#define CL_LIST_NO_END 100				//!< The end No. which can specify on the stored data in the instrument

// Number of elements on colorimetric value
#define CL_RENDERING_LEN 16				//!< The buffer size of color rendering index
#define CL_USERCUSTOM_LEN 4				//!< The number of data which can specify on custom color mode


//===========================
// Enumeration
//===========================
/*!
 * @brief The enumeration of the remote mode
 * @enum CL_REMOTEMODE
 */
typedef enum eCL_REMOTEMODE {
    CL_RMODE_OFF, //!< A remote mode is OFF
    CL_RMODE_ON, //!< A remote mode is ON
    CL_RMODE_NUM,

    CL_RMODE_FIRST = CL_RMODE_OFF,
    CL_RMODE_LAST = CL_RMODE_ON,
    CL_RMODE_DEFAULT = CL_RMODE_OFF
}
CL_REMOTEMODE;

/*!
 * @brief The enumeration of the key status
 * @enum CL_KEYSTATUS
 */
typedef enum eCL_KEYSTATUS {
    CL_KEY_STATE_OFF, //!< The key is not pressed
    CL_KEY_STATE_ON, //!< The key is pressed
}
CL_KEYSTATUS;

/*!
 * @brief The enumeration of the status of zero calibration
 * @enum CL_CALIBSTATUS
 */
typedef enum eCL_CALIBSTATUS {
    CL_CALIB_NA = 0, //!< A zero calibration is not able to perform
    CL_CALIB_OK, //!< A zero calibration is completed
    CL_CALIB_WR, //!< A zero calibration is recommended (It have passed a certain time from the last calibration)
    CL_CALIB_NG, //!< A zero calibration is not performed
    CL_CALIBSTATUS_NUM,
}
CL_CALIBSTATUS;

/*!
 * @brief The enumeration of the periodic calibration date
 * @enum CL_PERIODICCAL_TYPE
 */
typedef enum eCL_PERIODICCAL_TYPE {
    CL_PERIODICCAL_START = 0, //!< Start date on the periodic calibration
    CL_PERIODICCAL_END, //!< Expiration date on the periodic calibration
    CL_PERIODICCAL_NUM,
    CL_PERIODICCAL_FIRST = CL_PERIODICCAL_START,
    CL_PERIODICCAL_LAST = CL_PERIODICCAL_END
}
CL_PERIODICCAL_TYPE;

//----------------------
// System setting
//----------------------
/*!
 * @brief The enumeration on the system type
 * @enum CL_SYSTEMTYPE
 */
typedef enum eCL_SYSTEMTYPE {
    CL_SYSTEM_DATETIME, //!< Date and time
    CL_SYSTEM_DISPLAY, //!< Orientation of the display
    CL_SYSTEM_BEEP, //!< Buzzer setting
    CL_SYSTEM_LANGUAGE, //!< Display language
    CL_SYSTEM_DATEFORMAT, //!< Date display format
    CL_SYSTEM_UCAL_LIMIT, //!< Zero calibration expiry
    CL_SYSTEM_AUTOPOWEROFF, //!< Auto power off
    CL_SYSTEM_PCALNOTIFY, //!< Periodic calibration warning message
    CL_SYSTEM_NUM,
    CL_SYSTEM_FIRST = CL_SYSTEM_DATETIME,
    CL_SYSTEM_LAST = CL_SYSTEM_PCALNOTIFY
}
CL_SYSTEMTYPE;

/*!
 * @brief The enumeration of the orientation of the display
 * @enum CL_DISPLAYTYPE
 */
typedef enum eCL_DISPLAYTYPE {
    DISPLAY_NORMAL, //!< The LCD screen displays normal
    DISPLAY_INVERSE, //!< The LCD screen displays invert
    DISPLAY_NUM,
    DISPLAY_DEFAULT = DISPLAY_NORMAL,
    DISPLAY_FIRST = DISPLAY_NORMAL,
    DISPLAY_LAST = DISPLAY_INVERSE
}
CL_DISPLAYTYPE;

/*!
 * @brief The enumeration of the buzzer setting
 * @enum CL_BEEP
 */
typedef enum eBEEP {
    CL_BEEP_OFF, //!< The buzzer does not sound
    CL_BEEP_ON, //!< The buzzer sounds
    CL_BEEP_NUM,
    CL_BEEP_DEFAULT = CL_BEEP_ON,
    CL_BEEP_FIRST = CL_BEEP_OFF,
    CL_BEEP_LAST = CL_BEEP_ON
} CL_BEEP;


/*!
 * @brief The enumeration of the display language
 * @enum CL_LANGCODE
 */
typedef enum eCL_LANGCODE {
    CL_LANG_ENG, //!< Engilish
    CL_LANG_JPN, //!< Japanese
    CL_LANG_CHN, //!< Chinese
    CL_LANG_NUM, //!< the number of availabe languages
    CL_LANG_DEFAULT = CL_LANG_ENG, //!< default
    CL_LANG_FIRST = CL_LANG_ENG,
    CL_LANG_LAST = CL_LANG_CHN
}
CL_LANGCODE;

/*!
 * @brief The enumeration of the date display format
 * @enum CL_TYPE_DATEFORMAT
 */
typedef enum eCL_TYPE_DATEFORMAT {
    CL_TYPE_YYMMDD, //!< Display the date in year/month/day order
    CL_TYPE_MMDDYY, //!< Display the date in month/day/year order
    CL_TYPE_DDMMYY, //!< Display the date in day/month/year order
    CL_TYPE_NUM,
    CL_DATEFORMAT_DEFAULT = CL_TYPE_YYMMDD, //!< default
    CL_DATEFORMAT_FIRST = CL_TYPE_YYMMDD,
    CL_DATEFORMAT_LAST = CL_TYPE_DDMMYY,
}
CL_TYPE_DATEFORMAT;

/*!
 * @brief The enumeration of the zero calibration expiry
 * @enum CL_USERCAL_LIMIT
 */
typedef enum eCL_USERCAL_LIMIT {
    CL_USERCAL_LIMIT_3H, //!< The calibration prompt screen is displayed when elapsing 3 hour from last calibration
    CL_USERCAL_LIMIT_6H, //!< The calibration prompt screen is displayed when elapsing 6 hour from last calibration
    CL_USERCAL_LIMIT_12H, //!< The calibration prompt screen is displayed when elapsing 12 hour from last calibration
    CL_USERCAL_LIMIT_24H, //!< The calibration prompt screen is displayed when elapsing 24 hour from last calibration
    CL_USERCAL_LIMITLESS, //!< The calibration prompt screen is not displayed
    CL_USERCAL_LIMIT_NUM, //!< the number of availabe types
    CL_USERCAL_LIMIT_DEFAULT = CL_USERCAL_LIMIT_12H, //!< default
    CL_USERCAL_LIMIT_FIRST = CL_USERCAL_LIMIT_3H,
    CL_USERCAL_LIMIT_LAST = CL_USERCAL_LIMITLESS,
}
CL_USERCAL_LIMIT;

/*!
 * @brief The enumeration of the auto power off setting
 * @enum CL_AUTOPOWEROFF
 */
typedef enum eCL_AUTOPOWEROFF {
    CL_AUTOPOWEROFF_OFF = 0, //!< Disable the configuration of the auto power off
    CL_AUTOPOWEROFF_ON, //!< Enable the configuration of the auto power off
    CL_AUTOPOWEROFF_NUM,
    CL_AUTOPOWEROFF_DEFAULT = CL_AUTOPOWEROFF_ON,
    CL_AUTOPOWEROFF_FIRST = CL_AUTOPOWEROFF_OFF,
    CL_AUTOPOWEROFF_LAST = CL_AUTOPOWEROFF_ON
}
CL_AUTOPOWEROFF;

/*!
 * @brief The enumeration of the periodic calibration warning message
 * @enum CL_PCALNOTIFY
 */
typedef enum eCL_PCALNOTIFY {
    CL_PCALNOTIFY_OFF = 0, //!< Disables display of the periodic calibration warning message
    CL_PCALNOTIFY_ON, //!< Enables display of the periodic calibration warning message
    CL_PCALNOTIFY_NUM,
    CL_PCALNOTIFY_DEFAULT = CL_PCALNOTIFY_ON,
    CL_PCALNOTIFY_FIRST = CL_PCALNOTIFY_OFF,
    CL_PCALNOTIFY_LAST = CL_PCALNOTIFY_ON
}
CL_PCALNOTIFY;


//---------------------------------------------------
// Measurement condition in standalone measurement
//---------------------------------------------------

/*!
 * @brief The enumeration of the measurement condition type in standalone measurement
 * @enum CL_MEASSETTYPE
 */
typedef enum eCL_MEASSETTYPE {
    CL_MEASSET_DISPTYPE, //!< Display Type
    CL_MEASSET_OBS, //!< Observer
    CL_MEASSET_COLORSPACE, //!< Color Space
    CL_MEASSET_ILLUNIT, //!< Illuminance unit
    CL_MEASSET_EXPOSURETIME, //!< Measurement Time
    CL_MEASSET_USERCALIBCH, //!< User calibration CH
    CL_MEASSET_TARGETNO, //!< Target data No.
    CL_MEASSET_USERCUSTOM, //!< Custom color mode
    CL_MEASSET_MEASMODE, //!< Measurement mode ( SINGLE, MEAN, MULTI )
    CL_MEASSET_TIMERCONF, //!< timer configuration ( delay, interval, num of measurements )
    CL_MEASSET_USERWAVELENGTH, //!< arbitary wavelengths

    CL_MEASSET_NUM,

    CL_MEASSET_FIRST = CL_MEASSET_DISPTYPE,
    CL_MEASSET_LAST = CL_MEASSET_USERWAVELENGTH
}
CL_MEASSETTYPE;

/*!
 * @brief The enumeration of the display type on the instrument
 * @enum CL_DISP_TYPES
 */
typedef enum eCL_DISP_TYPES {
    CL_DISP_ABS, //!< Absolute
    CL_DISP_DIFF, //!< Difference
    CL_DISP_RANK, //!< Select Rank
    CL_DISP_NUM,

    CL_DISP_DEFAULT = CL_DISP_ABS,
    CL_DISP_FIRST = CL_DISP_ABS,
    CL_DISP_LAST = CL_DISP_RANK
}
CL_DISP_TYPES;

/*!
 * @brief The enumeration of the measurement time
 * @enum CL_MEASUREMENT_TIME
 */
typedef enum eCL_MEASUREMENT_TIME {
    CL_MEAS_TIME_FAST = 0, //!< FAST mode : The measurement time : 0.5 second
    CL_MEAS_TIME_SLOW, //!< SLOW mode : The measurement time : 2.5 second
    CL_MEAS_TIME_AUTO,
    //!< AUTO mode : Measures in accordance with the brightness of the light source. The measurement time : 0.5 to 27 seconds
    CL_MEAS_TIME_SUPER_FAST, //!< SUPER FAST mode : The measurement time : 0.2second
    CL_MEAS_TIME_NUM,

    CL_MEAS_TIME_DEFAULT = CL_MEAS_TIME_AUTO,
    CL_MEAS_TIME_FIRST = CL_MEAS_TIME_FAST,
    CL_MEAS_TIME_LAST = CL_MEAS_TIME_SUPER_FAST
} CL_MEASUREMENT_TIME;

/*!
 * @brief The enumeration of the illuminance units
 * @enum CL_ILLUMINANT_UNIT
 */
typedef enum eILLMINANT_UNIT {
    CL_ILLUNIT_LX = 0, //!< lux
    CL_ILLUNIT_FCD, //!< foot-candela
    CL_ILLUNIT_NUM,

    CL_ILLUNIT_DEFAULT = CL_ILLUNIT_LX,
    CL_ILLUNIT_FIRST = CL_ILLUNIT_LX,
    CL_ILLUNIT_LAST = CL_ILLUNIT_FCD
}
CL_ILLUMINANT_UNIT;

/*!
 * @brief The enumeration of the measurement condition by the CL-SDK
 * @enum CL_PROPERTIES
 */
typedef enum ePROPERTIES {
    CL_PR_OBSERVER, //!< Observer
    CL_PR_ILLUNIT, //!< Illuminance units
    CL_PR_NUM,

    CL_PR_FIRST = CL_PR_OBSERVER,
    CL_PR_LAST = CL_PR_ILLUNIT
}
CL_PROPERTIES;

/*!
 * @brief The enumeration of the implementation status of the measurement
 * @enum CL_MEASSTATUS
 */
typedef enum eCL_MEASSTATUS {
    CL_MEAS_FREE, //!< A measurement is not performed
    CL_MEAS_BUSY, //!< A measurement is performing
    CL_MEAS_FINISH //!< A measurement is completed
}
CL_MEASSTATUS;

/*!
 * @brief The enumeration of the implementation status of zero calibration
 * @enum CL_CALIBMEASSTATUS
 */
typedef enum eCL_CALIBMEASSTATUS {
    CL_CALIBMEAS_FREE, //!< A zero calibration is not performed
    CL_CALIBMEAS_BUSY, //!< A zero calibration is performing
    CL_CALIBMEAS_FINISH //!< A zero calibration is completed
}
CL_CALIBMEASSTATUS;

/*!
 * @brief The enumeration of type of the rank area
 * @enum CL_RANK_TYPE
 */
typedef enum eCL_RANK_TYPE {
    CL_RANK_CHROMA, //!< The rank area is specified by xy
    CL_RANK_COLORTEMP //!< The rank area is specified by Tcp/??uv
}
CL_RANK_TYPE;

/*!
 * @brief The enumeration of the color space which display on the instrument
 * @enum CL_COLOR_MODE
 */
typedef enum eCL_COLOR_MODE {
    CL_MODE_EVXY, //!< Ev, x, y
    CL_MODE_EVUV, //!< Ev, u?f, v?f
    CL_MODE_EVTCPDUV, //!< Ev, Correlated color temperature Tcp, duv
    CL_MODE_XYZ, //!< X, Y, Z
    CL_MODE_EVDWPE, //!< Ev, Dominant wavelength, Excitation purity Pe
    CL_MODE_RENDERING, //!< Color Rendering Index (Ra, R1 to R15)
    CL_MODE_SPECTRAL_GRAPH, //!< Spectral irradiance graph, Peak wavelength
    CL_MODE_CUSTOM, //!< Custom
    CL_MODE_NUM, //!<
    CL_MODE_FIRST = CL_MODE_EVXY,
    CL_MODE_LAST = CL_MODE_CUSTOM,
    CL_MODE_DEFAULT = CL_MODE_EVXY
}
CL_COLOR_MODE;

/*!
 * @brief The enumeration of the display items for custom color mode
 * @enum CL_CUSTOMDATA_ITEM
 */
typedef enum eCL_CUSTOMDATA_ITEM {
    CL_CUSTOM_NONE, //!< No display
    CL_CUSTOM_EV_DIFF, //!< Ev(Difference with target)
    CL_CUSTOM_EV_RATIO, //!< Ev(Percentage of target)
    CL_CUSTOM_SX, //!< x
    CL_CUSTOM_SY, //!< y
    CL_CUSTOM_U, //!< u'
    CL_CUSTOM_V, //!< v'
    CL_CUSTOM_TCP, //!< Correlated color temperature Tcp
    CL_CUSTOM_DUV, //!< duv
    CL_CUSTOM_LX_DIFF, //!< X(Difference with target)
    CL_CUSTOM_LX_RATIO, //!< X(Percentage of target)
    CL_CUSTOM_LY_DIFF, //!< Y(Difference with target)
    CL_CUSTOM_LY_RATIO, //!< Y(Percentage of target)
    CL_CUSTOM_LZ_DIFF, //!< Z(Difference with target)
    CL_CUSTOM_LZ_RATIO, //!< Z(Percentage of target)
    CL_CUSTOM_DW, //!< Dominant wavelength
    CL_CUSTOM_PE, //!< Excitation purity
    CL_CUSTOM_RANK, //!< Rank
    CL_CUSTOM_RA, //!< Ra
    CL_CUSTOM_R1, //!< R1
    CL_CUSTOM_R2, //!< R2
    CL_CUSTOM_R3, //!< R3
    CL_CUSTOM_R4, //!< R4
    CL_CUSTOM_R5, //!< R5
    CL_CUSTOM_R6, //!< R6
    CL_CUSTOM_R7, //!< R7
    CL_CUSTOM_R8, //!< R8
    CL_CUSTOM_R9, //!< R9
    CL_CUSTOM_R10, //!< R10
    CL_CUSTOM_R11, //!< R11
    CL_CUSTOM_R12, //!< R12
    CL_CUSTOM_R13, //!< R13
    CL_CUSTOM_R14, //!< R14
    CL_CUSTOM_R15, //!< R15
    //V1.2
    CL_CUSTOM_EV_SCOTOPIC_DIFF, //!< Scotopic Ev(Difference with target)
    CL_CUSTOM_EV_SCOTOPIC_RATIO, //!< Scotopic Ev(Percentage of target)
    CL_CUSTOM_SP, //!< Scotopic/Photopic Ratio
    CL_CUSTOM_EV_LAMBDA1, //!< Wavelength
    CL_CUSTOM_EV_LAMBDA2, //!< Wavelength
    CL_CUSTOM_EV_LAMBDA3, //!< Wavelength
    CL_CUSTOM_EV_LAMBDA4, //!< Wavelength

    CL_CUSTOM_NUM,
    CL_CUSTOM_FIRST = CL_CUSTOM_NONE,
    CL_CUSTOM_LAST = CL_CUSTOM_EV_LAMBDA4,
    CL_CUSTOM_DEFAULT1 = CL_CUSTOM_EV_RATIO,
    CL_CUSTOM_DEFAULT2 = CL_CUSTOM_TCP,
    CL_CUSTOM_DEFAULT3 = CL_CUSTOM_DW,
    CL_CUSTOM_DEFAULT4 = CL_CUSTOM_RA
}
CL_CUSTOMDATA_ITEM;


#define	CL_DELAY_TIMER_MIN	0			//!< ?x????????[?b]
#define	CL_DELAY_TIMER_MAX	999			//!< ?x????????[?b]

#define	CL_INTERBAL_TIMER_MIN	0		//!< ??????????[?b]
#define	CL_INTERBAL_TIMER_MAX	999		//!< ??????????[?b]

#define	CL_MEASURE_COUNT_MIN	0		//!< ??????(=?A??)
#define	CL_MEASURE_COUNT_MAX	100		//!< ??????[??]

typedef enum eCL_MESURE_MODE {
    CL_MESURE_MODE_SINGLE = 0, //!< ?V???O??
    CL_MESURE_MODE_AVERAGE, //!< ???
    CL_MESURE_MODE_CONTINUE, //!< ?A??

    CL_MESURE_MODE_NUM,
    CL_MESURE_MODE_FIRST = CL_MESURE_MODE_SINGLE,
    CL_MESURE_MODE_LAST = CL_MESURE_MODE_CONTINUE,
    CL_MESURE_MODE_DEFAULT = CL_MESURE_MODE_SINGLE,
}
CL_MESURE_MODE;

typedef enum eCL_MESURE_DISPLAY {
    CL_MESURE_DISPLAY_SINGLE_LOG = 0, //!< ????f?[?^?\??
    CL_MESURE_DISPLAY_AVERAGE, //!< ????\??

    CL_MESURE_DISPLAY_NUM,
    CL_MESURE_DISPLAY_FIRST = CL_MESURE_DISPLAY_SINGLE_LOG,
    CL_MESURE_DISPLAY_LAST = CL_MESURE_DISPLAY_AVERAGE,
    CL_MESURE_DISPLAY_DEFAULT = CL_MESURE_DISPLAY_SINGLE_LOG,
}
CL_MESURE_DISPLAY;

//===========================
// Struct & Union
//===========================

/*!
 * The structure of information on date and time
 */
typedef struct tCL_DEVDATETIME {
    uint32_km Year; //!< The year value
    uint32_km Month; //!< The month value
    uint32_km Day; //!< The day value
    uint32_km Hour; //!< The hour value
    uint32_km Minute; //!< The minute value
    uint32_km Second; //!< The seconds value
}
        CL_DEVDATETIME, CL_DATETIME;

/*!
 * The structure of the instrument information
 */
typedef struct tCL_DEVID {
    CL_PRODUCT_CODE Product[4]; //!< The product code
    CL_FACTORY_CODE Factory; //!< The factory code
    CL_SERIAL_CODE Serial; //!< The serial No. of instrument
    VERSION Firmware[RPG_FIRM_NO]; //!< The information of the firmware version
    CL_DATETIME FactoryDate; //!< The factory calibration date
    CL_VARIATION_CODE Variation; //!< The variation code
}
CL_DEVID;

/*!
 * The structure of user calibration coefficient
 */
typedef struct tCL_USERCALIB_DATA {
    real Coef[IRRADIANCE_LEN]; //!< The user calibration coefficient
    CL_DATETIME DateTime; //!< The date information
    int8_km Name[CL_USERCALIB_NAMESIZE]; //!< The calibration coefficient name
}
CL_USERCALIB_DATA;

/*!
 * The structure of system setting for the instrument
 */
typedef struct tCL_SYSTEMSETTING {
    CL_DATETIME Datetime; //!< The date and time setting for the instrument
    CL_DISPLAYTYPE Display; //!< Orientation of the display
    CL_BEEP Beep; //!< The buzzer setting for the instrument
    CL_LANGCODE Lang; //!< The language setting for the instrument
    CL_TYPE_DATEFORMAT DateFormat; //!< The date and time format for the instrument
    CL_USERCAL_LIMIT UserCalLimit; //!< Zero calibration expiry
    CL_AUTOPOWEROFF AutoPowerOff; //!< Auto power off setting
    CL_PCALNOTIFY PCalNotify; //!< Periodic calibration warning message
}
CL_SYSTEMSETTING;


/*!
 * The enum of measurement modes
 * @author rmiya
 */
typedef enum eCL_MEASMODE {
    CL_MEASMODE_SINGLE,
    CL_MEASMODE_AVERAGED,
    CL_MEASMODE_CONTINUOUS,

    CL_MEASMODE_FIRST = CL_MEASMODE_SINGLE,
    CL_MEASMODE_LAST = CL_MEASMODE_CONTINUOUS,
} CL_MEASMODE;

/*!
 * The struct of timer settings
 */
typedef struct tCL_TIMERCONF {
    uint16_km DelaySec;
    uint16_km Interval;
    uint16_km MeasNum;
} CL_TIMERCONF;

/*!
 * The struct of arbitary wavelengths
 */
typedef struct tCL_USERWAVELENGTH {
    uint16_km lambda[4];
} CL_USERWAVELENGTH;


/*!
 *  The structure of the measurement condition in standalone
 */
typedef struct tCL_MEASSETTING {
    CL_DISP_TYPES DispType; //!< Display type
    CL_OBSERVER Obs; //!< Observer in standalone measurement
    CL_COLOR_MODE ColorSpace; //!< Color mode in standalone measurement
    CL_ILLUMINANT_UNIT IlluminantUnit; //!< Illuminance units in the standalone measurement
    CL_MEASUREMENT_TIME ExposureTime; //!< The measurement time in standalone measurement
    int32_km UserCalibCh; //!< The user calibration CH in standalone measurement
    int32_km TargetNo; //!< The target data No. in standalone measurement
    CL_CUSTOMDATA_ITEM UserCustom[CL_USERCUSTOM_LEN]; //!< The items which display in custom color mode
    CL_MEASMODE MeasMode; //!< measurement mode ( SINGLE, MEAN, MULTI )
    CL_TIMERCONF TimerConf; //!< timer configuration ( delay, interval, the num of measurements )
    CL_USERWAVELENGTH UserWavelength; //!< arbitary wavelengths
}
CL_MEASSETTING;

/*!
 * The structure of key status
 */
typedef struct tCL_KEYINFO {
    CL_KEYSTATUS MeasKey; //!< The status of the Measuring button
    CL_KEYSTATUS UpKey; //!< The status of the Up key
    CL_KEYSTATUS DownKey; //!< The status of the Down key
    CL_KEYSTATUS BackKey; //!< The status of the Back key
    CL_KEYSTATUS EnterKey; //!< The status of the Enter key
}
CL_KEYINFO;

/*!
 * The structure of target data
 */
typedef struct tCL_TARGET_DATA {
    real SPCData[IRRADIANCE_LEN]; //!< Illuminance spectral data
    CL_DATETIME DateTime; //!< The stored date and time
    int8_km Name[CL_TARGET_NAMESIZE]; //!< Target data name
}
CL_TARGET_DATA;


//--------------------
// Measurement data
//--------------------
/*!
 * The structure of Evxy data
 */
typedef struct tCL_EvxyDATA {
    float Ev; //!< Ev
    float x; //!< x
    float y; //!< y
}
CL_EvxyDATA;

/*!
 * instrument information structure
 */
typedef struct tCL_EvuvDATA {
    float Ev; //!< Ev
    float u; //!< u?f
    float v; //!< v?f
}
CL_EvuvDATA;

/*!
 * The structure of Ev/Correlated color temperature/delta uv data
 */
typedef struct tCL_EvTduvDATA {
    float Ev; //!< Ev data
    float T; //!< Correlated color temperature
    float duv; //!< delta uv
}
CL_EvTduvDATA;

/*!
 * The structure of Ev/Dominant wavelength/Excitation purity data
 */
typedef struct tCL_EvDWPeDATA {
    float Ev; //!< Ev data
    float DW; //!< Dominant wavelength
    float Pe; //!< Excitation purity
}
CL_EvDWPeDATA;

/*!
 * The structure of color rendering index
 */
typedef struct tCL_RenderingDATA {
    float Data[CL_RENDERING_LEN]; //!< The color rendering index
}
CL_RenderingDATA;

/*!
 * The structure of Peak wavelength
 */
typedef struct tCL_PWDATA {
    float PeakWave; //!< Peak wavelength
}
CL_PWDATA;

/*!
 * The structure of illuminance spectral data
 */
typedef struct tCL_SPCDATA {
    real Data[IRRADIANCE_LEN]; //!< Illuminance spectral data
}
CL_SPCDATA;

/*!
 * The structure of XYZ data
 */
typedef struct tCL_XYZDATA {
    float X; //!< X
    float Y; //!< Y
    float Z; //!< Z
}
CL_XYZDATA;

/*!
 * The structure of Scotopic lux data
 */
typedef struct tCL_CL_ScotopicDATA {
    float Ev; //!< Ev  Photopic lux data
    float Es; //!< Ev' Scotopic lux data
    float SP; //!< S/P ratio
}
CL_ScotopicDATA;

/*!
 * The union of the measurement data
 */
typedef union tCL_MEASDATA {
    CL_EvxyDATA Evxy; //!< Ev/x/y data
    CL_EvuvDATA Evuv; //!< Ev/u?f/v
    CL_EvTduvDATA EvTduv; //!< Ev/Tcp/delta uv
    CL_EvDWPeDATA EvDWPe; //!< Ev/Dominant wavelength /Excitation purity
    CL_XYZDATA XYZ; //!< X/Y/Z
    CL_RenderingDATA Rendering; //!< Color rendering index
    CL_PWDATA Pw; //!< Peak wavelength
    CL_SPCDATA Spc; //!< Illuminance spectral data
    CL_ScotopicDATA Scotopic; //!< Ev/Ev'/SP
}
CL_MEASDATA;

//--------------------
// Color difference
//--------------------
/*!
 * The structure of color difference data on Ev/x/y
 */
typedef struct tCL_Evxy_DIFFDATA {
    float Ev_Abs; //!< Difference data of Ev (Difference with target)
    float Ev_Ratio; //!< Difference data of Ev (Percentage of target)
    float x; //!< Difference data of x
    float y; //!< Difference data of y
}
CL_Evxy_DIFFDATA;

/*!
 * The structure of color difference data on Ev/u?f/v?f
 */
typedef struct tCL_Evuv_DIFFDATA {
    float Ev_Abs; //!< Difference data of Ev (Difference with target)
    float Ev_Ratio; //!< Difference data of Ev (Percentage of target)
    float u; //!< Difference data of u?f
    float v; //!< Difference data of v?f
}
CL_Evuv_DIFFDATA;

/*!
 * The structure of color difference data on Ev/Tcp
 */
typedef struct tCL_EvTduv_DIFFDATA {
    float Ev_Abs; //!< Difference data of Ev (Difference with target
    float Ev_Ratio; //!< Difference data of Ev (Percentage of target)
    float T; //!< Difference data of Correlated color temperature
    float duv; //!< (Not used)
}
CL_EvTduv_DIFFDATA;

/*!
 * The structure of color difference data on Ev/Dominant wavelength/Excitation purity
 */
typedef struct tCL_EvDWPe_DIFFDATA {
    float Ev_Abs; //!< Difference data of Ev (Difference with target)
    float Ev_Ratio; //!< Difference data of Ev (Percentage of target)
    float DW; //!< Difference data of Dominant wavelength
    float Pe; //!< Difference data of Excitation purity
}
CL_EvDWPe_DIFFDATA;

/*!
 * The structure of color difference data on X/Y/Z
 */
typedef struct tCL_XYZ_DIFFDATA {
    float X_Abs; //!< Difference data of X (Difference with target)
    float Y_Abs; //!< Difference data of Y (Difference with target)
    float Z_Abs; //!< Difference data of Z (Difference with target)
    float X_Ratio; //!< Difference data of X (Percentage of target)
    float Y_Ratio; //!< Difference data of Y(Percentage of target)
    float Z_Ratio; //!< Difference data of Z (Percentage of target)
}
CL_XYZ_DIFFDATA;


/*!
 * The structure of color difference data on Ev/Es/SP
 */
typedef struct tCL_Scotopic_DIFFDATA {
    float Ev_Abs; //!< Difference data of Ev  (Difference with target)
    float Ev_Ratio; //!< Difference data of Ev  (Percentage of target)
    float Es_Abs; //!< Difference data of Es  (Difference with target)
    float Es_Ratio; //!< Difference data of Es  (Percentage of target)
    float SP_Abs; //!< Difference data of S/P (Difference of target)
}
CL_Scotopic_DIFFDATA;

/*!
 * The union of color difference data
 */
typedef union tCL_DIFFDATA {
    CL_Evxy_DIFFDATA Evxy; //!< Color difference data of Ev/x/y
    CL_Evuv_DIFFDATA Evuv; //!< Color difference data of Ev/u/v
    CL_EvTduv_DIFFDATA EvTduv; //!< Color difference data of Ev/Tcp
    CL_EvDWPe_DIFFDATA EvDWPe; //!< Color difference data of Ev/Dominant wavelength/ Excitation purity
    CL_XYZ_DIFFDATA XYZ; //!< Color difference data of X/Y/Z
    CL_RenderingDATA Rendering; //!< Color difference data of color rendering index
    CL_PWDATA Pw; //!< Color difference data of peak wavelength
    CL_Scotopic_DIFFDATA Scotopic; //!< Color difference data of Ev/Es/SP
}
CL_DIFFDATA;

//--------
// Rank
//--------
/*!
 * The structure of xy data which is used as rank data
 */
typedef struct tCL_xyDATA {
    float x; //!< x
    float y; //!< y
}
CL_xyDATA;

/*!
 * The structure of Tcp/deleta uv data which is used as rank data
 */
typedef struct tCL_TcpduvDATA {
    float Tcp; //!< Correlated color temperature
    float duv; //!< delta uv
}
CL_TcpduvDATA;

/*!
 * The structure of rank data which is used in sorting out the rank
 */
typedef struct tCL_RANK_DATA {
    CL_RANK_TYPE Type; //!< The point type which creates rank area (xy or Tcp/??uv)
    int8_km RankName[CL_RANK_NAMESIZE_SAVE]; //!< The rank name
    CL_xyDATA xyPoint[CL_RANK_POINTNUM]; //!< The array for configuring the rank area by xy data
    CL_TcpduvDATA TcpduvPoint[CL_RANK_POINTNUM]; //!< The array for configuring the rank area by Tcp/delta uv data
    int32_km PointNum; //!< The number of data which configures the rank area
    int32_km Enable; //!< The availability of when sorting out the rank
}
CL_RANK_DATA;


/*!
 * The structure of rank information which is sorted out
 */
typedef struct tCL_RANK {
    real Ev; //!< Ev data in measurement
    int8_km RankName[CL_RANK_NAMESIZE]; //!< Rank name of the corresponding rank
    int32_km RankNo; //!< The rank No. to be correspond
}
CL_RANK;

//---------------------------------
// Stored data in the instrument
//---------------------------------
/*!
 * The structure of the stored data in the instrument
 */
typedef struct tCL_LISTDATA {
    CL_MEASDATA Data; //!< Stored measurement data
    CL_DATETIME DateTime; //!< The date and time when saved the measurement data
    CL_OBSERVER Observer; //!< The observer when saved the measurement data
    int32_km OpCalibNo; //!< User calibration CH when saved the measurement data
    int32_km TargetNo; //!< Target No. when saved the measurement data
    CL_MEASUREMENT_TIME ExposureTime; //!< The measurement time at measurement
}
CL_LISTDATA;

#if defined(_WIN32) || defined(__APPLE__)
#pragma pack(pop)
#endif


#endif
