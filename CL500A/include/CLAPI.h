/** @brief      The definition file of the CL-SDK interface
                
    @file       CLAPI.h
    @author     KONICA MINOLTA, INC.

	Copyright(c) 2012-2016 KONICA MINOLTA, INC. All rights reserved.

*/


#ifndef CL_API_H
#define CL_API_H

#include "TypeDefine.h"
#include "CLConditions.h"
#include "CLColorConditions.h"
#include "Version.h"
#include "ErrorDefine.h"

#if defined(__cplusplus)
extern "C"{
#endif


/*! 
 * @brief Gets the object handle of the instrument which is connected on the PC
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @return ER_CODE
 */
ER_CODE KMAPI CLOpenDevice(DEVICE_HANDLE* hDevice);

/*! 
 * @brief Releases the object handle of the instrument which is stored in the CL-SDK
 * @param[in] hDevice	: The object handle to be released
 * @return ER_CODE
 */
ER_CODE KMAPI CLCloseDevice(DEVICE_HANDLE hDevice);

/*! 
 * @brief Configure a remote mode ON/OFF
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Mode		: The configuration of remote mode
 * @return ER_CODE
 */
ER_CODE KMAPI CLSetRemoteMode(DEVICE_HANDLE hDevice, CL_REMOTEMODE Mode);

/*! 
 * @brief Gets the remote mode ON/OFF
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] pMode	: The buffer to store a remote mode setting
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetRemoteMode(DEVICE_HANDLE hDevice, CL_REMOTEMODE* pMode);


/*! 
 * @brief Performs a measurement
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] pTime	: The buffer to store a measurement time
 * @return ER_CODE
 */
ER_CODE KMAPI CLDoMeasurement(DEVICE_HANDLE hDevice, int32_km* pTime);

/*! 
 * @brief Performs a measurement by specifying exposure time and cumulative num of measurements
 * @param[in] hDevice		: The object handle of the instrument to be controlled
 * @param[in] ExposureTime	: Exposure Time [x100us]
 * @param[in] MeasTimes		: cumltative number of measurements [times]
 * @return ER_CODE
 * @author rmiya
 */
ER_CODE KMAPI CLDoManualMeasurement(DEVICE_HANDLE hDevice, int32_km ExposureTime, int32_km MeasTimes);

/*! 
 * @brief Confirms the implementation status of measurement
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] pStatus	: The buffer to store the measurement status
 * @return ER_CODE
 */
ER_CODE KMAPI CLPollingMeasure(DEVICE_HANDLE hDevice, CL_MEASSTATUS* pStatus);

/*! 
 * @brief Stops a measurement
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @return ER_CODE
 */
ER_CODE KMAPI CLStopMeasurement(DEVICE_HANDLE hDevice);

/*! 
 * Setting the measurement condition to the instrument
 * @brief Performs a measurement with all instrument
 * @param[out] pTime	: The buffer to store a measurement time
 * @return ER_CODE
 */
ER_CODE KMAPI CLDoMeasurementAll(int32_km* pTime);

/*! 
 * Setting the measurement condition to the instrument
 * @brief Performs a measurement with all instrument by specifying exposure time and cumulative num of measurements
 * @param[in] ExposureTime	: Exposure Time [x100us]
 * @param[in] MeasTimes		: cumltative number of measurements [times]
 * @return ER_CODE
 * @author rmiya
 */
ER_CODE KMAPI CLDoManualMeasurementAll(int32_km ExposureTime, int32_km MeasNum);

/*! 
 * @brief Confirms the implementation status of a measurement by CLDoMeasurementAll()
 * @param[out] pStatus	: The buffer to store the measurement status
 * @return ER_CODE
 */
ER_CODE KMAPI CLPollingMeasureAll(CL_MEASSTATUS* pStatus);

/*! 
 * @brief Stops a measurement by CLDoMeasurementAll()
 * @return ER_CODE
 */
ER_CODE KMAPI CLStopMeasurementAll();

/*! 
 * @brief Performs a zero calibration
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @return ER_CODE
 */
ER_CODE KMAPI CLDoCalibration(DEVICE_HANDLE hDevice);

/*! 
 * @brief Gets the implementation status of a zero calibration
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] pStatus	: The buffer to store the status of a zero calibration
 * @return ER_CODE
 */
ER_CODE KMAPI CLPollingCalibration(DEVICE_HANDLE hDevice, CL_CALIBMEASSTATUS* pStatus);

/*! 
 * @brief Gets a status whether a zero calibration have performed
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] Status	: The buffer to store the calibration status
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetCalibrateStatus(DEVICE_HANDLE hDevice, CL_CALIBSTATUS* Status);

/*! 
 * @brief Gets the each colorimetric data at the latest measurement
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The colorimetric type to be obtained
 * @param[out] pColor	: The buffer to store a colorimetric data
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetMeasData(DEVICE_HANDLE hDevice, CL_COLORSPACE Type, CL_MEASDATA* pColor);

/*! 
 * @brief Gets each color difference data at the latest measurement
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The color difference type to be obtained
 * @param[out] pDiff	: The buffer to store the color difference
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetColorDifference(DEVICE_HANDLE hDevice, CL_COLORSPACE Type, CL_DIFFDATA* pDiff);

/*! 
 * @brief Selects rank for the measurement data
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] Rank		: The buffer to store the rank information
 * @return ER_CODE
 */
ER_CODE KMAPI CLSortOutRank(DEVICE_HANDLE hDevice, CL_RANK* Rank);

/*! 
 * Registers a rank data whch is used when selecting rank
 * @brief Registers a rank data which is used when selecting rank
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: The Data No. which register a rank data
 * @param[in] RankData	: The rank data to be registered
 * @return ER_CODE
 */
ER_CODE KMAPI CLSetRankData(DEVICE_HANDLE hDevice, int32_km DataNo, const CL_RANK_DATA* RankData);

/*! 
 * @brief Gets the rank data which is registered in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: The rank No. of the rank data to be obtained
 * @param[out] RankData	: The buffer to store rank data
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetRankData(DEVICE_HANDLE hDevice, int32_km DataNo, CL_RANK_DATA* RankData);

/*! 
 * @brief Deletes the rank data which is registered in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: The data No. to be deleted
 * @return ER_CODE
 */
ER_CODE KMAPI CLDeleteRankData(DEVICE_HANDLE hDevice, int32_km DataNo);

/*! 
 * @brief Registers a target data to the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: The data No. of the target data to be registered
 * @param[in] pTarget	: The target data to be registered
 * @return ER_CODE
 */
ER_CODE KMAPI CLSetTargetData(DEVICE_HANDLE hDevice, const int32_km DataNo, const CL_TARGET_DATA* pTarget);

/*! 
 * @brief Gets the target data which is registered in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: The data No. of the target data to be obtained
 * @param[out] pTarget	: The buffer to store the target data
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetTargetData(DEVICE_HANDLE hDevice, int32_km DataNo, CL_TARGET_DATA* pTarget);

/*! 
 * @brief Deletes the target data which is registered in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: The target data No. to be deleted
 * @return ER_CODE
 */
ER_CODE KMAPI CLDeleteTargetData(DEVICE_HANDLE hDevice, int32_km DataNo);

/*! 
 * @brief Gets the number of stored data in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] Num		: The buffer to store the number of measurement data
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetDeviceStoredDataNum(DEVICE_HANDLE hDevice, int32_km* Num);

/*! 
 * @brief Gets all the stored data in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled 
 * @param[out] pData	: The buffer to store the measurement data in the instrument
 * @param[in] Type		: The colorimetric type to be obtained
 * @param[in] Length	: The buffer size
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetDeviceStoredData(DEVICE_HANDLE hDevice, CL_LISTDATA* pData, CL_COLORSPACE Type, int32_km Length);

/*! 
 * @brief Deletes the stored data in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled 
 * @param[in] DataNo	: The stored data No. to be deleted
 * @return ER_CODE
 */
ER_CODE KMAPI CLDeleteDeviceStoredData(DEVICE_HANDLE hDevice, int32_km DataNo);

/*! 
 * Setting the measurement condition to the instrument
 * @brief Registers a user calibration coefficient to the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: User calibration CH to be registered
 * @param[in] pCoef		: The user calibration coefficient to be registered
 * @return ER_CODE
 */
ER_CODE KMAPI CLSetUserCalibrationData(DEVICE_HANDLE hDevice, int32_km DataNo, const CL_USERCALIB_DATA* pCoef);

/*! 
 * @brief Gets the user calibration coefficient which is registered in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: User calibration CH to be obtained
 * @param[out] pCoef	: The buffer to store the user calibration coefficient
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetUserCalibrationData(DEVICE_HANDLE hDevice, int32_km DataNo, CL_USERCALIB_DATA* pCoef);

/*! 
 * Setting the measurement condition to the instrument
 * @brief Deletes a user calibration coefficient which is registered in the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] DataNo	: User calibration CH to be deleted
 * @return ER_CODE
 */
ER_CODE KMAPI CLDeleteUserCalibrationData(DEVICE_HANDLE hDevice, int32_km DataNo);

/*! 
 * @brief Calculates a user calibration coefficients
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] Output	: The buffer to store the calculated user calibration coefficient
 * @param[in] Target	: The target data for calculation
 * @param[in] Sample	: The measurement data for calculation
 * @return ER_CODE
 */
ER_CODE KMAPI CLCalcUserCalibrationData(DEVICE_HANDLE hDevice, CL_SPCDATA* Output, const CL_SPCDATA* Target, const CL_SPCDATA* Sample);

/*! 
 * @brief Configures the measurement condition when control the instrument by the CL-SDK
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The property type to be configured
 * @param[in] Param		: The property value to be configured
 * @return ER_CODE
 */
ER_CODE KMAPI CLSetProperty(DEVICE_HANDLE hDevice, CL_PROPERTIES Type, int32_km Param);

/*! 
 * @brief Gets the measurement condition when control the instrument by the CL-SDK
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The property type to be obtained
 * @param[out] pParam	: The buffer to store the property value
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetProperty(DEVICE_HANDLE hDevice, CL_PROPERTIES Type, int32_km* pParam);

/*! 
 * @brief Gets the key status for instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] pStatus	: The buffer to store the key status
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetButtonStatus(DEVICE_HANDLE hDevice, CL_KEYINFO* pStatus);

/*! 
 * @brief Configures the measurement condition in standalone measurement
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The measurement condition type to be configured 
 * @param[in] pSetting	: The measurement condition to be configured
 * @return ER_CODE
 */
ER_CODE KMAPI CLSetMeasSetting(DEVICE_HANDLE hDevice, CL_MEASSETTYPE Type, const CL_MEASSETTING* pSetting);

/*! 
 * @brief Gets the measurement condition in standalone measurement
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The measurement condition type to be obtained 
 * @param[out] pSetting	: The buffer to store a measurement condition
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetMeasSetting(DEVICE_HANDLE hDevice, CL_MEASSETTYPE Type, CL_MEASSETTING* pSetting);

/*! 
 * @brief Configures the system setting of the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The system setting type to be configured
 * @param[in] pSetting	: The system setting to be configured
 * @return ER_CODE
 */
ER_CODE KMAPI CLSetSystemSetting(DEVICE_HANDLE hDevice, CL_SYSTEMTYPE Type, const CL_SYSTEMSETTING* pSetting);

/*! 
 * @brief Gets the system setting of the instrument
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[in] Type		: The system setting type to be obtained
 * @param[out] pSetting	: The buffer to store the system setting
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetSystemSetting(DEVICE_HANDLE hDevice, CL_SYSTEMTYPE Type, CL_SYSTEMSETTING* pSetting);

/*! 
 * @brief Gets the instrument information
 * @param[in] hDevice		: The object handle of the instrument to be controlled
 * @param[out] pDeviceID	: The buffer to store the instrument information
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetDeviceID(DEVICE_HANDLE hDevice, CL_DEVID* pDeviceID);

/*! 
 * @brief Gets the version information of the CL-SDK
 * @param[out] SDKVersion	: The buffer to store the version information
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetSDKVersion(CL_SDKVERSION *SDKVersion);

/*! 
 * @brief Gets a detail of warning at the latest processing
 * @param[in] hDevice	: The object handle of the instrument to be controlled
 * @param[out] wrcode	: The buffer to store a warning details
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetWarning(DEVICE_HANDLE hDevice, WR_CODE* wrcode);

/*! 
 * @brief Gets the information about the periodic calibration date
 * @param[in] hDevice		: The object handle of the instrument to be controlled
 * @param[in] Type			: Type of periodic calibration date
 * @param[out] pDateTime	: The buffer to store the calibration date
 * @return ER_CODE
 */
ER_CODE KMAPI CLGetPeriodicCalDate(DEVICE_HANDLE hDevice, CL_PERIODICCAL_TYPE Type, CL_DATETIME* pDateTime);


#if defined(__cplusplus)
}
#endif

#endif /* CL_API_H*/
