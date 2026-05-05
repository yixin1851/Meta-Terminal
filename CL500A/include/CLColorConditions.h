/** @brief      The definition file of the information on calculating color
                
    @file       CLColorConditions.h
    @author     KONICA MINOLTA, INC.

	Copyright(c) 2012-2016 KONICA MINOLTA, INC. All rights reserved.
*/

#ifndef _CLCOLORCONDITIONS_H_
#define _CLCOLORCONDITIONS_H_

//===========================
// The definition value
//===========================

#define SPC_LENGTH(max,min,interval)	((max-min)/interval+1)
//!< The start wavelength for illuminance spectral data
#define IRRADIANCE_BEGIN	360
//!< The end wavelength for illuminance spectral data
#define IRRADIANCE_END		780
//!< The wavelength pitch for illuminance spectral data
#define IRRADIANCE_PITCH	1
//!< The number of illuminance spectral data 
#define IRRADIANCE_LEN		SPC_LENGTH(IRRADIANCE_END,IRRADIANCE_BEGIN,IRRADIANCE_PITCH)

//!< The value to be obtained when exceeds measurement range by the CL-500A
#define CL_OVER_ERROR_VALUE -10000.0f
//!< The value to be obtained when measure the light source which cannot be calculated the correlated color temperature
#define CL_INCOMPUTABLE_VALUE -11000.0f

//===========================
// Enumeration
//===========================

/*!
 * The enumeration of observer 
 */
typedef enum eCL_OBSERVER {
    CL_OBS_02DEG = 0, //!< 2 degree
    CL_OBS_10DEG, //!< 10 degree
    CL_OBS_NUM,

    CL_OBS_FIRST = CL_OBS_02DEG,
    CL_OBS_LAST = CL_OBS_10DEG,
    CL_OBS_DEFAULT = CL_OBS_02DEG,
}
CL_OBSERVER;


/*!
 * The enumeration of color space
 */
typedef enum eCL_COLORSPACE {
    CL_COLORSPACE_EVXY = 0, //!< Ev, x, y
    CL_COLORSPACE_EVUV, //!< Ev, u�f, v�f
    CL_COLORSPACE_EVTCPJISDUV, //!< Ev, Correlated color temperature Tcp(JIS), delta uv
    CL_COLORSPACE_EVTCPDUV, //!< Ev, Correlated color temperature Tcp, delta uv
    CL_COLORSPACE_EVDWPE, //!< Ev, Dominant wavelength, Excitation purity
    CL_COLORSPACE_XYZ, //!< X, Y, Z
    CL_COLORSPACE_RENDERING, //!< Color Rendering Index (Ra, R1 to R15)
    CL_COLORSPACE_PW, //!< Peak wavelength
    CL_COLORSPACE_SPC, //!< Illuminance spectral data
    CL_COLORSPACE_SCOTOPIC, //!< Ev, Ev', S/P ratio
    CL_COLORSPACE_NUM,

    CL_COLORSPACE_FIRST = CL_COLORSPACE_EVXY,
    CL_COLORSPACE_LAST = CL_COLORSPACE_SCOTOPIC,
    CL_COLORSPACE_DEFAULT = CL_COLORSPACE_EVXY
}
CL_COLORSPACE;


#endif
