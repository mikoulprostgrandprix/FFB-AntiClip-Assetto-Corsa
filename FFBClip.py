
## Sjekk at combos.ini lagres med rett format



#Libraries
import ac
import acsys
import os
import sys
import configparser
import traceback
import csv
import math

Version="6.4.0-ui1"

#Variable initialization - FFBCLIP
Histogram = []
ffbMultiplier = 1
AutoMode=1
OldGain=1
Cutoff=0.01
CarGainTarget=1
OldRAW=0
OldCarGain=0
DynamicMode=0
OldFFBMultiplier=1
DynamicTarget=1
OptionsPage=0
DynamicThreshold=1.5
DynamicSpeed=0.01
TargetGain=1.0
MaxTorque=20.0
TrackID=""
TrackConfigID=""
CarID=""
DDToggle=0
ManualOverride=0
DDMappingVersion=0

# Advanced modes (v6)
AdaptiveMode=0          # 0=classic, 1=lock, 2=hybrid
LearnLaps=4             # number of completed laps used for learning
LockPercentile=20       # percentile of the LOW values distribution
HybridBand=0.15         # +/- band around lock baseline
LearningLapStart=-1
LearningComplete=0
LearningSamples=[]
LearningSafeCaps=[]
LockValue=1.0
LastLapCount=-1

# v6.2 - optional advanced features (all toggleable)
FeatureProfileMode=1
FeaturePhaseLearning=1
FeatureOutlierFilter=1
FeatureAntiOscillation=1
FeatureSafetyLimits=1
FeatureAutoResetCombo=1
FeatureLearningConfidence=1
FeatureEnduranceMode=1
FeatureCSVLogging=0
FeaturePresetManager=1

ProfileMode=0              # 0=Race, 1=Qualif
AutoProfileSession=1       # auto switch qualif/race when possible

SafetyFloor=0.25
SafetyCeiling=2.50

OutlierWindow=[]
OutlierWindowSize=25
OutlierSigma=3.0

OscillationDeadband=0.01
OscillationMinInterval=0.15
LastAppliedGainChange=0.0
LastGainApplyTime=0.0

LearningSamplesSlow=[]
LearningSamplesMid=[]
LearningSamplesFast=[]

EnduranceStartTime=0.0
EnduranceMinutes=35.0
EnduranceDropMax=0.12

LastCSVLogTime=0.0
CSVLogInterval=1.0
CSVPath='apps/python/FFBClip/Config/ffbclip_runtime_log.csv'

PresetName='default'
LastComboKey=''

# v6.3 - additional 10 advanced features (all toggleable)
FeatureWetMode=1
FeatureKerbFilter=1
FeatureSetupAwareLearning=1
FeatureConfidenceGate=1
FeatureRollbackOneClick=1
FeatureResponseCurves=1
FeatureAdvancedAntiFatigue=1
FeatureDiagnosticDashboard=1
FeatureCalibrationAssistant=1
FeatureSessionReport=1

WetGripThreshold=0.90
WetSoftening=0.12
KerbSpikeThreshold=0.30
KerbDampFactor=0.65
SetupHash=''
ConfidenceGateThreshold=0.75
RollbackGain=1.0
RollbackLockValue=1.0
ResponseCurveMode=0          # 0=linear, 1=expo, 2=s-curve
ResponseCurveStrength=0.35
AntiFatigueLowBand=0.45
AntiFatigueHighBand=0.90
AntiFatigueReduction=0.10
DiagRefreshSeconds=1.0
LastDiagTime=0.0
CalibrationState=0           # 0=off,1=warmup,2=learning,3=validation
CalibrationLapStart=-1
CalibrationWarmupLaps=1
CalibrationLearnLaps=2
CalibrationValidationLaps=1
SessionReportPath='apps/python/FFBClip/Config/ffbclip_session_report.txt'
RuntimeMinutesEstimate=0.0
RunClock=0.0
LastStatusMessage=""
LastDetailMessage=""
OptionsTab=0
MainPageWidgets=[]
OptionsNavWidgets=[]
OptionsDriveWidgets=[]
OptionsAdaptiveWidgets=[]
OptionsProtectionWidgets=[]
OptionsToolsWidgets=[]
OptionsActionWidgets=[]


#Variable initialization - AC
dT=0
dTG=0
ffbMultiplierSmoothOld=1
DynamicAdd=0
RB=0
GraphForceHistory=[]
GraphTargetHistory=[]
GraphHistorySize=180
GraphAreaX=12
GraphAreaY=112
GraphAreaW=336
GraphAreaH=124
PeakForceWindow=0.0
GraphPeakForceWindow=0.0
ClipOutputLimit=0.98
GraphValueMin=-0.05
GraphValueMax=2.10
DDUsableTorqueRatio=(12.0/18.0)



def _clamp(v, lo, hi):
	return max(lo, min(hi, v))


def _dd_nominal_ratio():
	return _clamp(DDUsableTorqueRatio, 0.20, 1.00)


def _dd_ratio_to_nm(ratio):
	scale = _dd_nominal_ratio()
	return _clamp((float(ratio) / max(scale, 0.01)) * float(MaxTorque), 3, 50)


def _dd_nm_to_ratio(nm_value):
	return _clamp((float(nm_value) / max(float(MaxTorque), 0.1)) * _dd_nominal_ratio(), 0.0, 3.0)


def _needs_dd_mapping_migration():
	return DDToggle == 1 and int(DDMappingVersion) < 2


def _migrate_dd_legacy_ratio(ratio):
	ratio = _clamp(float(ratio), 0.0, 3.0)
	if _needs_dd_mapping_migration():
		return _clamp(ratio * _dd_nominal_ratio(), 0.0, 3.0)
	return ratio


def _commit_dd_mapping_migration():
	global DDMappingVersion, TargetGain, CarGainTarget, CarGain, LockValue
	if not _needs_dd_mapping_migration():
		return
	WriteOptions(FFBClip,FFBClipPath,"Options","targetgain",str(TargetGain))
	WriteOptions(FFBClip,FFBClipPath,"targetgains",CarID,str(CarGainTarget))
	WriteOptions(FFBClip,FFBClipPath,"Options","ddmappingversion","2")
	DDMappingVersion = 2
	if os.path.exists(ComboPath):
		WriteOptions(Combo,ComboPath,_combo_section_name(),CarID,str(CarGain))
		if AdaptiveMode != 0 and LearningComplete == 1:
			WriteOptions(Combo,ComboPath,_combo_section_name(),_combo_lock_option_name(),str(LockValue))


def _percentile(values, p):
	if not values:
		return 1.0
	sorted_vals = sorted(values)
	p = _clamp(float(p), 0.0, 100.0)
	k = (len(sorted_vals) - 1) * (p / 100.0)
	f = int(math.floor(k))
	c = int(math.ceil(k))
	if f == c:
		return sorted_vals[f]
	d0 = sorted_vals[f] * (c - k)
	d1 = sorted_vals[c] * (k - f)
	return d0 + d1


def _learning_status_text():
	global AdaptiveMode, LearningComplete, LearningLapStart, LearnLaps, LastLapCount, LockValue
	if AdaptiveMode == 0:
		return "Classic mode"
	if LearningComplete == 1:
		if AdaptiveMode == 1:
			return "Lock mode active @ {:.0%}".format(LockValue)
		return "Hybrid mode active @ {:.0%}".format(LockValue)
	if LearningLapStart < 0:
		return "Learning pending"
	done = max(0, LastLapCount - LearningLapStart)
	remaining = max(0, int(LearnLaps) - done)
	return "Learning laps: {} left".format(remaining)


def _update_learning_state(current_gain_sample, safe_cap_sample=None):
	global AdaptiveMode, LearningLapStart, LearningComplete, LearningSamples, LearningSafeCaps, LearnLaps
	global LockPercentile, LockValue, LastLapCount, FeaturePhaseLearning
	global RollbackGain, RollbackLockValue
	if AdaptiveMode == 0:
		return False
	try:
		lap_count = int(ac.getCarState(0, acsys.CS.LapCount))
	except Exception:
		return False
	LastLapCount = lap_count
	if LearningComplete == 1:
		return False
	if LearningLapStart < 0:
		LearningLapStart = lap_count
	if current_gain_sample > 0:
		LearningSamples.append(float(current_gain_sample))
		if FeaturePhaseLearning==1:
			_phase_bucket(float(current_gain_sample))
		safe_cap = safe_cap_sample
		if safe_cap is None:
			safe_cap = _compute_peak_safe_gain(current_gain_sample, max(CurrentForce, PeakForceWindow), _clamp(CarGainTarget, 0.05, 1.20))
		safe_cap = float(safe_cap)
		LearningSafeCaps.append(_clamp(safe_cap, 0.20, 3.0))
	required = max(1, int(LearnLaps))
	if (lap_count - LearningLapStart) >= required and len(LearningSamples) > 20:
		recent_count = min(len(LearningSamples), 80)
		recent_samples = LearningSamples[-recent_count:]
		recent_safe_caps = LearningSafeCaps[-recent_count:] if LearningSafeCaps else []
		base_lock = _percentile(recent_samples, LockPercentile)
		safe_lock = min(recent_safe_caps) if recent_safe_caps else base_lock
		LockValue = min(base_lock, safe_lock * 0.99)
		LockValue = _clamp(LockValue, 0.20, 3.0)
		LearningComplete = 1
		RollbackGain = _clamp(_percentile(recent_samples, max(35.0, LockPercentile)), 0.20, 2.50)
		RollbackLockValue = LockValue
		_persist_combo_lock(LockValue)
		return True
	return False

def _safe_get_session_type():
	try:
		st = ac.getSessionType()
		return str(st).lower()
	except Exception:
		return ""


def _apply_profile_mode():
	global ProfileMode, DynamicSpeed, DynamicThreshold
	if ProfileMode == 1:  # Qualif
		DynamicSpeed = _clamp(DynamicSpeed * 1.15, 0.003, 0.08)
		DynamicThreshold = _clamp(DynamicThreshold * 1.12, 1.0, 3.0)
	else:  # Race
		DynamicSpeed = _clamp(DynamicSpeed * 0.92, 0.003, 0.08)
		DynamicThreshold = _clamp(DynamicThreshold * 0.95, 1.0, 3.0)


def _auto_profile_from_session():
	global ProfileMode
	s = _safe_get_session_type()
	if 'qual' in s or 'hotlap' in s or 'practice' in s:
		ProfileMode = 1
	elif 'race' in s:
		ProfileMode = 0


def _robust_outlier_filter(v):
	global OutlierWindow
	if v <= 0:
		return v
	OutlierWindow.append(float(v))
	if len(OutlierWindow) > OutlierWindowSize:
		OutlierWindow.pop(0)
	if len(OutlierWindow) < 8:
		return v
	sw = sorted(OutlierWindow)
	m = sw[len(sw)//2]
	dev = [abs(x - m) for x in sw]
	md = sorted(dev)[len(dev)//2] + 1e-9
	if abs(v - m) > (OutlierSigma * 1.4826 * md):
		return m
	return v


def _phase_bucket(sample):
	try:
		speed = float(ac.getCarState(0, acsys.CS.SpeedKMH))
	except Exception:
		speed = 120.0
	if speed < 90:
		LearningSamplesSlow.append(sample)
	elif speed < 170:
		LearningSamplesMid.append(sample)
	else:
		LearningSamplesFast.append(sample)


def _phase_percentile_lock():
	p_s = _percentile(LearningSamplesSlow, LockPercentile) if LearningSamplesSlow else None
	p_m = _percentile(LearningSamplesMid, LockPercentile) if LearningSamplesMid else None
	p_f = _percentile(LearningSamplesFast, LockPercentile) if LearningSamplesFast else None
	vals=[]
	weights=[]
	for v,w in ((p_s,0.30),(p_m,0.45),(p_f,0.25)):
		if v is not None:
			vals.append(v); weights.append(w)
	if not vals:
		return 1.0
	w = sum(weights) if sum(weights)>0 else 1.0
	return sum(v*(weights[i]/w) for i,v in enumerate(vals))


def _learning_confidence():
	alln = len(LearningSamples)
	if alln < 30:
		return 0.2
	if alln < 80:
		return 0.5
	if alln < 140:
		return 0.75
	return 1.0


def _apply_endurance_ceiling(base_ceiling):
	global EnduranceStartTime
	if EnduranceStartTime <= 0:
		EnduranceStartTime = ac.getCarState(0, acsys.CS.LapTime) if hasattr(acsys.CS,'LapTime') else 0
	try:
		elapsed_s = float(ac.getCarState(0, acsys.CS.RaceTimeLeft))
		# unreliable on all sessions; fallback below if weird
		if elapsed_s < 0:
			raise Exception()
	except Exception:
		# fallback pseudo timer with app delta accumulation unavailable here: use lap count heuristic
		try:
			elapsed_s = float(ac.getCarState(0, acsys.CS.LapCount)) * 120.0
		except Exception:
			elapsed_s = 0.0
	start_after = EnduranceMinutes * 60.0
	if elapsed_s <= start_after:
		return base_ceiling
	ratio = _clamp((elapsed_s - start_after) / (start_after + 1.0), 0.0, 1.0)
	drop = EnduranceDropMax * ratio
	return base_ceiling * (1.0 - drop)


def _csv_log_line(ffb_t, ffb_s, car_gain):
	global LastCSVLogTime, RunClock
	now_t = RunClock
	if now_t - LastCSVLogTime < CSVLogInterval:
		return
	LastCSVLogTime = now_t
	head = not os.path.exists(CSVPath)
	with open(CSVPath, 'a') as f:
		if head:
			f.write('lapTime,profile,mode,learningComplete,lockValue,target,smooth,carGain,confidence\n')
		f.write('{:.3f},{},{},{},{:.4f},{:.4f},{:.4f},{:.4f},{:.3f}\n'.format(now_t,ProfileMode,AdaptiveMode,LearningComplete,LockValue,ffb_t,ffb_s,car_gain,_learning_confidence()))


def _load_preset_if_needed():
	global FFBClip, FFBClipPath, PresetName
	global AdaptiveMode, LearnLaps, LockPercentile, HybridBand, DynamicThreshold, DynamicSpeed
	sec = 'Preset_' + PresetName
	FFBClip.read(FFBClipPath)
	if not FFBClip.has_section(sec):
		return
	for key in ('adaptivemode','learnlaps','lockpercentile','hybridband','dynamicthreshold','dynamicspeed'):
		if FFBClip.has_option(sec,key):
			value = FFBClip.get(sec,key)
			WriteOptions(FFBClip,FFBClipPath,'Options',key,value)
			if key == 'adaptivemode':
				AdaptiveMode = int(float(value))
			elif key == 'learnlaps':
				LearnLaps = int(float(value))
			elif key == 'lockpercentile':
				LockPercentile = float(value)
			elif key == 'hybridband':
				HybridBand = float(value)
			elif key == 'dynamicthreshold':
				DynamicThreshold = float(value)
			elif key == 'dynamicspeed':
				DynamicSpeed = float(value)


def _save_preset_snapshot():
	global FFBClip, FFBClipPath, PresetName
	sec = 'Preset_' + PresetName
	if not FFBClip.has_section(sec):
		FFBClip.add_section(sec)
	for key in ('adaptivemode','learnlaps','lockpercentile','hybridband','dynamicthreshold','dynamicspeed'):
		if FFBClip.has_option('Options',key):
			FFBClip.set(sec,key,FFBClip.get('Options',key))
	with open(FFBClipPath,'w') as cf:
		FFBClip.write(cf)



def _normalize01(v, lo, hi):
	v = float(v)
	if hi <= lo:
		return 0.0
	return _clamp((v - lo) / (hi - lo), 0.0, 1.0)


def _apply_response_curve(v):
	global ResponseCurveMode, ResponseCurveStrength
	x = _clamp(v, 0.0, 3.0)
	n = _normalize01(x, 0.0, 3.0)
	k = _clamp(ResponseCurveStrength, 0.0, 1.0)
	if ResponseCurveMode == 1:  # expo
		n2 = n ** (1.0 + 2.0 * k)
	elif ResponseCurveMode == 2:  # soft s-curve
		n2 = (1-k)*n + k*(3*n*n - 2*n*n*n)
	else:
		n2 = n
	return _clamp(n2 * 3.0, 0.0, 3.0)


def _apply_wet_softening(v):
	global WetGripThreshold, WetSoftening
	try:
		grip = float(ac.getCarState(0, acsys.CS.TyreGrip))
	except Exception:
		grip = 1.0
	if grip < WetGripThreshold:
		drop = _clamp((WetGripThreshold - grip), 0.0, 0.30)
		f = 1.0 - (WetSoftening * (drop / 0.30))
		return v * _clamp(f, 0.75, 1.0)
	return v


def _apply_kerb_filter(v, current_force):
	global KerbSpikeThreshold, KerbDampFactor, OldRAW
	spike = abs(current_force - OldRAW)
	if spike > KerbSpikeThreshold:
		return v * _clamp(KerbDampFactor, 0.35, 1.0)
	return v


def _compute_setup_hash():
	global CarID, TrackID, TrackConfigID, MaxTorque, TargetGain, DynamicThreshold, DynamicSpeed
	parts = [CarID, TrackID, TrackConfigID, str(round(MaxTorque,2)), str(round(TargetGain,3)), str(round(DynamicThreshold,3)), str(round(DynamicSpeed,4))]
	return '|'.join(parts)


def _confidence_gate_passed():
	global ConfidenceGateThreshold
	return _learning_confidence() >= _clamp(ConfidenceGateThreshold,0.5,0.98)


def _diag_line(ffb_t, ffb_s, car_gain, conf_value=None):
	clip_ratio = 1.0 if ffb_t >= 0.99 else 0.0
	vol = abs(ffb_s - car_gain)
	if conf_value is None:
		conf_value = _learning_confidence()
	return "clip {:.0%} | vol {:.2f} | mode {} | conf {:.0%}".format(clip_ratio, vol, AdaptiveMode, conf_value)


def _set_message_if_changed(msg):
	global LastStatusMessage
	if msg != LastStatusMessage:
		ac.setText(messageLabel, msg)
		LastStatusMessage = msg


def _update_calibration_assistant():
	global CalibrationState, CalibrationLapStart, CalibrationWarmupLaps, CalibrationLearnLaps, CalibrationValidationLaps
	global LearningLapStart, LearningComplete, LearningSamples, LearningSamplesSlow, LearningSamplesMid, LearningSamplesFast
	if CalibrationState == 0:
		return
	try:
		lap = int(ac.getCarState(0, acsys.CS.LapCount))
	except Exception:
		return
	if CalibrationLapStart < 0:
		CalibrationLapStart = lap
		return
	d = lap - CalibrationLapStart
	if CalibrationState == 1 and d >= CalibrationWarmupLaps:
		CalibrationState = 2
		LearningLapStart = lap
		LearningComplete = 0
		LearningSamples = []
		LearningSamplesSlow = []
		LearningSamplesMid = []
		LearningSamplesFast = []
	elif CalibrationState == 2 and d >= (CalibrationWarmupLaps + CalibrationLearnLaps):
		CalibrationState = 3
	elif CalibrationState == 3 and d >= (CalibrationWarmupLaps + CalibrationLearnLaps + CalibrationValidationLaps):
		CalibrationState = 0


def _maybe_write_session_report():
	global SessionReportPath, RuntimeMinutesEstimate
	try:
		laps = int(ac.getCarState(0, acsys.CS.LapCount))
	except Exception:
		laps = 0
	lines=[]
	lines.append('FFBClip Session Report')
	lines.append('Version: '+Version)
	lines.append('Laps: {}'.format(laps))
	lines.append('AdaptiveMode: {}'.format(AdaptiveMode))
	lines.append('LearningComplete: {}'.format(LearningComplete))
	lines.append('LockValue: {:.4f}'.format(LockValue))
	lines.append('Confidence: {:.2%}'.format(_learning_confidence()))
	lines.append('Runtime(min est): {:.1f}'.format(RuntimeMinutesEstimate))
	with open(SessionReportPath,'w') as f:
		f.write("\n".join(lines))


def _set_visible(controls, visible):
	state = 1 if visible else 0
	for control in controls:
		if control:
			ac.setVisible(control, state)


def _style_window():
	ac.drawBorder(appWindow, 1)
	ac.setBackgroundColor(appWindow, 0.10, 0.12, 0.16)
	ac.setBackgroundOpacity(appWindow, 0.98)


def _style_label(label, size=12, color=(0.96, 0.97, 1.0, 1.0)):
	ac.setFontSize(label, size)
	ac.setFontColor(label, color[0], color[1], color[2], color[3])
	ac.setBackgroundOpacity(label, 0)


def _style_button(button, active=False, accent=False):
	if accent:
		bg = (0.22, 0.50, 0.84) if active else (0.22, 0.26, 0.33)
	elif active:
		bg = (0.20, 0.42, 0.24)
	else:
		bg = (0.24, 0.28, 0.34)
	ac.setFontSize(button, 12)
	ac.setFontColor(button, 1.0, 1.0, 1.0, 1)
	ac.setBackgroundColor(button, bg[0], bg[1], bg[2])
	ac.setBackgroundOpacity(button, 1.0)
	ac.drawBorder(button, 1)


def _style_spinner(spinner):
	ac.setBackgroundColor(spinner, 0.20, 0.24, 0.30)
	ac.setBackgroundOpacity(spinner, 1.0)
	ac.setFontColor(spinner, 1.0, 1.0, 1.0, 1)
	ac.drawBorder(spinner, 1)


def _style_checkbox(checkbox):
	ac.setFontSize(checkbox, 12)
	ac.setFontColor(checkbox, 0.96, 0.97, 1.0, 1)
	ac.setBackgroundOpacity(checkbox, 0)


def _draw_panel(x, y, w, h, color):
	ac.glColor4f(color[0], color[1], color[2], color[3])
	ac.glQuad(x, y, w, h)


def _push_graph_sample(force_value, target_value):
	force_value = _clamp(force_value, GraphValueMin, GraphValueMax)
	target_value = _clamp(target_value, GraphValueMin, GraphValueMax)
	if not GraphForceHistory:
		GraphForceHistory.extend([force_value] * GraphHistorySize)
		GraphTargetHistory.extend([target_value] * GraphHistorySize)
		return
	GraphForceHistory.pop(0)
	GraphForceHistory.append(force_value)
	GraphTargetHistory.pop(0)
	GraphTargetHistory.append(target_value)


def _draw_line_strip(points, color):
	if len(points) < 2:
		return
	ac.glColor4f(color[0], color[1], color[2], color[3])
	for idx in range(1, len(points)):
		x1, y1 = points[idx - 1]
		x2, y2 = points[idx]
		ac.glBegin(acsys.GL.Lines)
		ac.glVertex2f(x1, y1)
		ac.glVertex2f(x2, y2)
		ac.glEnd()


def _draw_graph_border(x, y, w, h, color):
	_draw_panel(x, y, w, 1, color)
	_draw_panel(x, y + h - 1, w, 1, color)
	_draw_panel(x, y, 1, h, color)
	_draw_panel(x + w - 1, y, 1, h, color)


def _apply_car_gain_target(target_ratio):
	current_ratio = round(ac.getCarFFB()/100.0, 4)
	target_ratio = _clamp(target_ratio, 0.0, 3.0)
	delta_ratio = target_ratio - current_ratio
	if abs(delta_ratio) > 0.0005:
		ac.setCarFFB(delta_ratio * 100.0)


def _combo_section_name():
	return TrackID + "_" + TrackConfigID


def _combo_lock_option_name():
	return CarID + "_lock"


def _persist_combo_lock(lock_ratio):
	global Combo, ComboPath
	lock_ratio = _clamp(lock_ratio, 0.20, 3.0)
	WriteOptions(Combo, ComboPath, _combo_section_name(), _combo_lock_option_name(), "{:.4f}".format(lock_ratio))


def _clear_combo_lock():
	global Combo, ComboPath
	Combo.read(ComboPath)
	if Combo.has_section(_combo_section_name()) and Combo.has_option(_combo_section_name(), _combo_lock_option_name()):
		Combo.remove_option(_combo_section_name(), _combo_lock_option_name())
		with open(ComboPath, 'w') as configfile:
			Combo.write(configfile)


def _load_combo_lock():
	global Combo, ComboPath, AdaptiveMode, LearningComplete, LearningLapStart, LockValue
	global RollbackGain, RollbackLockValue, LearningSamples, LearningSamplesSlow, LearningSamplesMid, LearningSamplesFast, LearningSafeCaps
	Combo.read(ComboPath)
	if not Combo.has_section(_combo_section_name()):
		return False
	if not Combo.has_option(_combo_section_name(), _combo_lock_option_name()):
		return False
	try:
		lock_ratio = float(Combo.get(_combo_section_name(), _combo_lock_option_name()))
	except Exception:
		return False
	LockValue = _clamp(_migrate_dd_legacy_ratio(lock_ratio), 0.20, 3.0)
	RollbackGain = LockValue
	RollbackLockValue = LockValue
	LearningComplete = 1 if AdaptiveMode != 0 else 0
	LearningLapStart = -1
	LearningSamples = [LockValue] * 160
	LearningSamplesSlow = [LockValue] * 48
	LearningSamplesMid = [LockValue] * 72
	LearningSamplesFast = [LockValue] * 40
	LearningSafeCaps = [LockValue] * 160
	return True


def _compute_peak_safe_gain(current_gain, peak_force, target_force):
	current_gain = _clamp(current_gain, 0.0, 3.0)
	target_force = _clamp(target_force, 0.05, 1.20)
	peak_force = max(0.0, peak_force)
	if peak_force <= 0.0001:
		return current_gain
	desired_gain = current_gain * (target_force / max(peak_force, 0.05))
	return _clamp(desired_gain, 0.0, 3.0)


def _compute_learning_gain_target(current_gain, peak_force, target_force):
	current_gain = _clamp(current_gain, 0.0, 3.0)
	target_force = _clamp(target_force, 0.05, 1.20)
	peak_force = max(0.0, peak_force)
	if peak_force > (target_force * 1.005):
		desired_gain = _compute_peak_safe_gain(current_gain, peak_force, target_force)
	else:
		headroom = _clamp((target_force - peak_force) / target_force, 0.0, 1.0)
		step_up = 0.004 + (0.020 * headroom)
		desired_gain = current_gain + step_up
	ce = SafetyCeiling if FeatureSafetyLimits==1 else 3.0
	fl = SafetyFloor if FeatureSafetyLimits==1 else 0.0
	return _clamp(desired_gain, fl, ce)


def _draw_realtime_graph():
	x = GraphAreaX
	y = GraphAreaY
	w = GraphAreaW
	h = GraphAreaH
	_draw_panel(x, y, w, h, (0.12, 0.13, 0.15, 0.96))
	_draw_graph_border(x, y, w, h, (0.55, 0.58, 0.62, 0.9))
	_draw_panel(x + 1, y + (h / 2), w - 2, 1, (0.28, 0.31, 0.36, 0.9))
	_draw_panel(x + 1, y + (h * 0.25), w - 2, 1, (0.22, 0.25, 0.29, 0.8))
	_draw_panel(x + 1, y + (h * 0.75), w - 2, 1, (0.22, 0.25, 0.29, 0.8))
	if len(GraphForceHistory) < 2:
		return
	scale_min = GraphValueMin
	scale_max = GraphValueMax
	scale_span = max(0.01, scale_max - scale_min)
	force_points = []
	target_points = []
	span = float(max(1, len(GraphForceHistory) - 1))
	for idx, value in enumerate(GraphForceHistory):
		px = x + 2 + ((w - 4) * (idx / span))
		py = y + h - 2 - ((h - 4) * _clamp((value - scale_min) / scale_span, 0.0, 1.0))
		force_points.append((px, py))
	for idx, value in enumerate(GraphTargetHistory):
		px = x + 2 + ((w - 4) * (idx / span))
		py = y + h - 2 - ((h - 4) * _clamp((value - scale_min) / scale_span, 0.0, 1.0))
		target_points.append((px, py))
	_draw_line_strip(target_points, (1.0, 0.22, 0.22, 1.0))
	_draw_line_strip(force_points, (0.30, 1.0, 0.30, 1.0))
	if force_points:
		px, py = force_points[-1]
		_draw_panel(px - 1, py - 1, 3, 3, (0.75, 1.0, 0.75, 1.0))


def _adaptive_mode_text():
	if AdaptiveMode == 1:
		return "Lock"
	if AdaptiveMode == 2:
		return "Hybrid"
	return "Classic"


def _profile_mode_text():
	return "Qualif" if ProfileMode == 1 else "Race"


def _response_curve_text():
	if ResponseCurveMode == 1:
		return "Expo"
	if ResponseCurveMode == 2:
		return "S-curve"
	return "Linear"


def _display_mode_text():
	if DisplayMode == 1:
		return "Graph"
	if DisplayMode == 2:
		return "Histogram"
	return "Off"


def _target_spinner_value():
	if DDToggle == 1:
		return _dd_ratio_to_nm(CarGainTarget)
	if Cutoff > 0.01 and CarGainTarget >= 1.0:
		return _clamp((1.0 + Cutoff) * 100.0, 10, 120)
	return _clamp(CarGainTarget * 100.0, 10, 120)


def _default_spinner_value():
	if DDToggle == 1:
		return _dd_ratio_to_nm(TargetGain)
	return _clamp(TargetGain * 100.0, 10, 120)


def _set_detail_if_changed(msg):
	global LastDetailMessage
	if msg != LastDetailMessage:
		ac.setText(detailLabel, msg)
		LastDetailMessage = msg


def _sync_gain_controls():
	if DDToggle == 1:
		ac.setText(StrengthLabel, "Torque target (Nm)")
		ac.setText(DefaultgainSpinnerLabel, "Default torque target (Nm)")
		ac.setRange(targetGainSpinner, 3, 50)
		ac.setRange(DefaultGainSpinner, 3, 50)
		ac.setVisible(TorqueSpinner, 1 if OptionsPage == 1 and OptionsTab == 0 else 0)
	else:
		ac.setText(StrengthLabel, "FFB Strength")
		ac.setText(DefaultgainSpinnerLabel, "Default FFB strength (%)")
		ac.setRange(targetGainSpinner, 10, 120)
		ac.setRange(DefaultGainSpinner, 10, 120)
		ac.setVisible(TorqueSpinner, 0)
	ac.setValue(targetGainSpinner, _target_spinner_value())
	ac.setValue(DefaultGainSpinner, _default_spinner_value())


def _reset_learning_state(status_message=None, clear_persisted=False):
	global LearningLapStart, LearningComplete, LearningSamples, LearningSamplesSlow, LearningSamplesMid, LearningSamplesFast, LearningSafeCaps, LockValue
	LearningLapStart = -1
	LearningComplete = 0
	LearningSamples = []
	LearningSamplesSlow = []
	LearningSamplesMid = []
	LearningSamplesFast = []
	LearningSafeCaps = []
	LockValue = 1.0
	if clear_persisted:
		_clear_combo_lock()
	if status_message:
		_set_message_if_changed(status_message)


def _update_tab_styles():
	_style_button(DriveTabButton, OptionsTab == 0, True)
	_style_button(AdaptiveTabButton, OptionsTab == 1, True)
	_style_button(ProtectionTabButton, OptionsTab == 2, True)
	_style_button(ToolsTabButton, OptionsTab == 3, True)


def _refresh_graph_visibility():
	graph_visible = OptionsPage == 0 and DisplayMode > 0
	ac.setVisible(graph, 1 if (graph_visible and DisplayMode == 2) else 0)
	_set_visible([summaryLabel, summaryLabel2], OptionsPage == 0 and not graph_visible)


def _refresh_ui_text():
	ac.setText(AutoModeButton, "Mode: Auto" if AutoMode == 1 else "Mode: Manual")
	ac.setText(DynamicButton, "Dynamic: ON" if DynamicMode == 1 else "Dynamic: OFF")
	ac.setText(DisplaymodeButton, _display_mode_text())
	ac.setText(AdaptiveModeButton, _adaptive_mode_text())
	ac.setText(ProfileModeButton, _profile_mode_text())
	ac.setText(ResponseCurveModeButton, _response_curve_text())
	ac.setText(CalibrationButton, "Stop calib" if CalibrationState > 0 else "Start calib")
	ac.setText(OptionTitleLabel, ("Drive & Session", "Adaptive Learning", "Protection", "Response & Tools")[OptionsTab])
	status_parts = ["AUTO" if AutoMode == 1 else "MANUAL", _adaptive_mode_text().upper()]
	if DynamicMode == 1:
		status_parts.append("DYN")
	ac.setText(StatusBadgeLabel, " | ".join(status_parts))
	if AutoMode == 1:
		ac.setFontColor(StatusBadgeLabel, 0.55, 0.90, 0.62, 1)
	else:
		ac.setFontColor(StatusBadgeLabel, 0.98, 0.72, 0.32, 1)
	_style_button(AutoModeButton, AutoMode == 1)
	_style_button(DynamicButton, DynamicMode == 1)
	_style_button(DisplaymodeButton, DisplayMode > 0, True)
	_style_button(AdaptiveModeButton, AdaptiveMode > 0, True)
	_style_button(ProfileModeButton, ProfileMode == 1, True)
	_style_button(ResponseCurveModeButton, ResponseCurveMode > 0, True)
	_style_button(CalibrationButton, CalibrationState > 0)
	track_name = TrackID if TrackConfigID == "" else "{} / {}".format(TrackID, TrackConfigID)
	ac.setText(ComboLabel, "{}  |  {}".format(CarID, track_name))
	profile_text = "auto" if AutoProfileSession == 1 else "manual"
	_set_detail_if_changed("Profile {} ({}) | Curve {} | Display {}".format(_profile_mode_text(), profile_text, _response_curve_text(), _display_mode_text()))
	ac.setText(summaryLabel, "Combo {:.0%} | Default {:.0%} | Safety {:.0%}-{:.0%}".format(CarGainCombo, TargetGain, SafetyFloor, SafetyCeiling))
	cal_text = ("off", "warmup", "learn", "validate")[int(_clamp(CalibrationState, 0, 3))]
	ac.setText(summaryLabel2, "Wet {} | Kerb {} | Diag {} | Cal {}".format("on" if FeatureWetMode == 1 else "off", "on" if FeatureKerbFilter == 1 else "off", "on" if FeatureDiagnosticDashboard == 1 else "off", cal_text))
	_update_tab_styles()
	_refresh_graph_visibility()


def _show_option_tab(tab):
	global OptionsTab
	OptionsTab = int(_clamp(tab, 0, 3))
	_set_visible(OptionsDriveWidgets, OptionsTab == 0)
	_set_visible(OptionsAdaptiveWidgets, OptionsTab == 1)
	_set_visible(OptionsProtectionWidgets, OptionsTab == 2)
	_set_visible(OptionsToolsWidgets, OptionsTab == 3)
	_sync_gain_controls()
	_refresh_ui_text()


def _set_options_page(opened):
	global OptionsPage
	OptionsPage = 1 if opened else 0
	_set_visible(MainPageWidgets, not opened)
	_set_visible(OptionsNavWidgets, opened)
	_set_visible(OptionsActionWidgets, opened)
	if opened:
		ac.setSize(appWindow, 460, 470)
		ac.setPosition(OptionsButton, 342, 434)
		ac.setSize(OptionsButton, 106, 24)
		ac.setText(OptionsButton, "Close")
		_show_option_tab(OptionsTab)
	else:
		_set_visible(OptionsDriveWidgets, 0)
		_set_visible(OptionsAdaptiveWidgets, 0)
		_set_visible(OptionsProtectionWidgets, 0)
		_set_visible(OptionsToolsWidgets, 0)
		ac.setSize(appWindow, 360, 300)
		ac.setPosition(OptionsButton, 270, 266)
		ac.setSize(OptionsButton, 78, 24)
		ac.setText(OptionsButton, "Options")
	ac.setVisible(OptionsButton, 1)
	_refresh_graph_visibility()
	_refresh_ui_text()


def _toggle_calibration():
	global CalibrationState, CalibrationLapStart
	if FeatureCalibrationAssistant == 0 and CalibrationState == 0:
		_set_message_if_changed("Enable calibration helper before starting calibration")
		return
	if CalibrationState > 0:
		CalibrationState = 0
		CalibrationLapStart = -1
		_set_message_if_changed("Calibration assistant stopped")
	else:
		CalibrationState = 1
		CalibrationLapStart = -1
		_reset_learning_state(clear_persisted=True)
		_set_message_if_changed("Calibration assistant armed")
	_refresh_ui_text()


def _apply_rollback():
	if RollbackGain <= 0:
		_set_message_if_changed("Rollback unavailable until learning has data")
		return
	value = _clamp(_dd_ratio_to_nm(RollbackGain) if DDToggle == 1 else RollbackGain * 100.0, 3 if DDToggle == 1 else 10, 50 if DDToggle == 1 else 120)
	targetChange(value)
	ac.setValue(targetGainSpinner, value)
	_apply_car_gain_target(RollbackGain)
	_set_message_if_changed("Rollback target applied")

def acMain(acVersion):

	global Version ,appWindow
	global messageLabel,detailLabel,summaryLabel,summaryLabel2,targetGainSpinner,gainLabel,DynamicButton,AutoModeButton,DDToggleButton,ManualToggle,ResetButton,DefaultGainSpinner,TorqueSpinner,OptionsButton
	global TitleLabel,ComboLabel,StatusBadgeLabel,OptionTitleLabel,OptionHintLabel,DriveTabButton,AdaptiveTabButton,ProtectionTabButton,ToolsTabButton
	global CalibrationButton,ResetLearningButton,RollbackButton,ProfileModeButton,ResponseCurveModeButton
	global DefaultgainSpinnerLabel, StrengthLabel,GraphRefreshSpinner,DisplaymodeButtonLabel,DisplaymodeButton,DynamicThresholdSpinner,DynamicSpeedSpinner
	global AdaptiveModeLabel,AdaptiveModeButton,LearnLapsSpinner,LockPercentileSpinner,HybridBandSpinner,ConfidenceGateSpinner,ProfileModeLabel,ResponseCurveModeLabel
	global SafetyFloorSpinner,SafetyCeilingSpinner,OscillationDeadbandSpinner,OscillationMinIntervalSpinner,EnduranceMinutesSpinner,EnduranceDropSpinner
	global WetGripSpinner,WetSofteningSpinner,KerbSpikeSpinner,KerbDampSpinner,ResponseCurveStrengthSpinner,AntiFatigueLowSpinner,AntiFatigueHighSpinner,AntiFatigueReductionSpinner,DiagRefreshSpinner
	global CalibrationWarmupSpinner,CalibrationLearnSpinner,CalibrationValidationSpinner
	global FeatureWetToggle,FeatureKerbToggle,FeatureSetupToggle,FeatureConfidenceToggle,FeatureRollbackToggle,FeatureCurveToggle,FeatureFatigueToggle,FeatureDiagToggle,FeatureCalibToggle,FeatureReportToggle
	global FeatureCSVToggle,FeaturePresetToggle,FeatureProfileToggle,FeaturePhaseToggle,FeatureOutlierToggle,FeatureOscillationToggle,FeatureSafetyToggle,FeatureEnduranceToggle,FeatureLearningToggle,FeatureAutoResetToggle,AutoProfileToggle
	global MainPageWidgets,OptionsNavWidgets,OptionsDriveWidgets,OptionsAdaptiveWidgets,OptionsProtectionWidgets,OptionsToolsWidgets,OptionsActionWidgets
	global errorMessage,graph
	global CarGainTarget,ffbMultiplier,Histogram,MainGain,TargetGain,CarGainCombo,OldCarGain,ComboGain,TargetCarGain
	global AutoMode,DynamicMode,ManualOverride,DDToggle,MaxTorque
	global TrackID,TrackConfigID,CarID,CarGain,config,Combo,ComboPath,FFBClip,FFBClipPath
	global DynamicSpeed,DynamicThreshold,GraphRefresh,DisplayMode,RB,RBToggle
	global GraphForceHistory,GraphTargetHistory
	global AdaptiveMode,LearnLaps,LockPercentile,HybridBand,LearningLapStart,LearningComplete,LearningSamples,LockValue,LastLapCount
	global FeatureProfileMode,FeaturePhaseLearning,FeatureOutlierFilter,FeatureAntiOscillation,FeatureSafetyLimits,FeatureAutoResetCombo,FeatureLearningConfidence,FeatureEnduranceMode,FeatureCSVLogging,FeaturePresetManager
	global ProfileMode,AutoProfileSession,SafetyFloor,SafetyCeiling,OscillationDeadband,OscillationMinInterval,EnduranceMinutes,EnduranceDropMax,PresetName,LastComboKey
	global FeatureWetMode,FeatureKerbFilter,FeatureSetupAwareLearning,FeatureConfidenceGate,FeatureRollbackOneClick,FeatureResponseCurves,FeatureAdvancedAntiFatigue,FeatureDiagnosticDashboard,FeatureCalibrationAssistant,FeatureSessionReport
	global WetGripThreshold,WetSoftening,KerbSpikeThreshold,KerbDampFactor,SetupHash,ConfidenceGateThreshold,RollbackGain,RollbackLockValue,ResponseCurveMode,ResponseCurveStrength,AntiFatigueLowBand,AntiFatigueHighBand,AntiFatigueReduction,DiagRefreshSeconds,CalibrationState,CalibrationLapStart,CalibrationWarmupLaps,CalibrationLearnLaps,CalibrationValidationLaps,SessionReportPath

	
	ac.log("## FFBClip section start")
	#Intializing configparser
	config = configparser.ConfigParser()
	Combo = configparser.ConfigParser()
	UserFF = configparser.ConfigParser()
	FFBClip = configparser.ConfigParser()
	
	userffPath = os.path.expanduser(r"~\Documents\Assetto Corsa\cfg\user_ff.ini")
	ComboPath= "apps/python/FFBClip/Config/Combos.ini"
	FFBClipPath="apps/python/FFBClip/Config/FFBClip.ini"

	#initialize the Histogram
	for n in range(0,300):
		Histogram.append(0)
	GraphForceHistory = []
	GraphTargetHistory = []

	
#Get the car name 
	CarID = str(ac.getCarName(0) or "")
	TrackID = str(ac.getTrackName(0) or "")
	tc = ac.getTrackConfiguration(0)
	TrackConfigID = str(tc) if tc is not None else ""
	ac.log("Car ID: " + CarID + ", Track ID: " + TrackID + ", TrackConfigID: " + TrackConfigID)
	LastComboKey = TrackID+"_"+TrackConfigID+"::"+CarID
	
	#Read the ini file and set appropriate default values if they don't exist
	if not os.path.exists(FFBClipPath):
		with open(FFBClipPath, 'w') as configfile:
			ac.log("FFBClip.ini not found, creating")
			FFBClip.write(configfile)
			ac.log("FFBClip.ini created")
	FFBClip.read(FFBClipPath)
	ac.log("FFBClip.ini read:")

## FFBClip section
	TargetGain = float(ReadOptions(FFBClip, FFBClipPath, "Options", "targetgain", "1"))
	DynamicMode = float(ReadOptions(FFBClip, FFBClipPath, "Options", "dynamicmode", "0"))
	MaxTorque = float(ReadOptions(FFBClip, FFBClipPath, "Options", "maxtorque", "20"))
	DynamicThreshold = float(ReadOptions(FFBClip, FFBClipPath, "Options", "dynamicthreshold", "2"))
	DynamicSpeed = float(ReadOptions(FFBClip, FFBClipPath, "Options", "dynamicspeed", "0.01"))
	GraphRefresh = float(ReadOptions(FFBClip, FFBClipPath, "Options", "graphrefresh", "2"))
	DisplayMode = float(ReadOptions(FFBClip, FFBClipPath, "Options", "displaymode", "0"))
	RB = float(ReadOptions(FFBClip, FFBClipPath, "Options", "rb", "0"))
	AdaptiveMode = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "adaptivemode", "0")))
	LearnLaps = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "learnlaps", "3")))
	LockPercentile = float(ReadOptions(FFBClip, FFBClipPath, "Options", "lockpercentile", "25"))
	HybridBand = float(ReadOptions(FFBClip, FFBClipPath, "Options", "hybridband", "0.20"))
	FeatureProfileMode = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_profilemode", "1")))
	FeaturePhaseLearning = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_phaselearning", "1")))
	FeatureOutlierFilter = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_outlierfilter", "1")))
	FeatureAntiOscillation = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_antioscillation", "1")))
	FeatureSafetyLimits = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_safetylimits", "1")))
	FeatureAutoResetCombo = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_autoresetcombo", "1")))
	FeatureLearningConfidence = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_learningconfidence", "1")))
	FeatureEnduranceMode = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_endurancemode", "1")))
	FeatureCSVLogging = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_csvlogging", "0")))
	FeaturePresetManager = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_presetmanager", "1")))
	ProfileMode = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "profilemode", "0")))
	AutoProfileSession = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "autoprofilesession", "1")))
	SafetyFloor = float(ReadOptions(FFBClip, FFBClipPath, "Options", "safetyfloor", "0.25"))
	SafetyCeiling = float(ReadOptions(FFBClip, FFBClipPath, "Options", "safetyceiling", "2.50"))
	OscillationDeadband = float(ReadOptions(FFBClip, FFBClipPath, "Options", "oscillationdeadband", "0.01"))
	OscillationMinInterval = float(ReadOptions(FFBClip, FFBClipPath, "Options", "oscillationmininterval", "0.15"))
	EnduranceMinutes = float(ReadOptions(FFBClip, FFBClipPath, "Options", "enduranceminutes", "35"))
	EnduranceDropMax = float(ReadOptions(FFBClip, FFBClipPath, "Options", "endurancedropmax", "0.12"))
	PresetName = ReadOptions(FFBClip, FFBClipPath, "Options", "presetname", "default")
	FeatureWetMode = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_wetmode", "1")))
	FeatureKerbFilter = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_kerbfilter", "1")))
	FeatureSetupAwareLearning = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_setupawarelearning", "1")))
	FeatureConfidenceGate = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_confidencegate", "1")))
	FeatureRollbackOneClick = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_rollbackoneclick", "1")))
	FeatureResponseCurves = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_responsecurves", "1")))
	FeatureAdvancedAntiFatigue = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_advancedantifatigue", "1")))
	FeatureDiagnosticDashboard = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_diagnosticdashboard", "1")))
	FeatureCalibrationAssistant = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_calibrationassistant", "1")))
	FeatureSessionReport = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "feature_sessionreport", "1")))
	WetGripThreshold = float(ReadOptions(FFBClip, FFBClipPath, "Options", "wetgripthreshold", "0.90"))
	WetSoftening = float(ReadOptions(FFBClip, FFBClipPath, "Options", "wetsoftening", "0.12"))
	KerbSpikeThreshold = float(ReadOptions(FFBClip, FFBClipPath, "Options", "kerbspikethreshold", "0.30"))
	KerbDampFactor = float(ReadOptions(FFBClip, FFBClipPath, "Options", "kerbdampfactor", "0.65"))
	ConfidenceGateThreshold = float(ReadOptions(FFBClip, FFBClipPath, "Options", "confidencegatethreshold", "0.75"))
	ResponseCurveMode = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "responsecurvemode", "0")))
	ResponseCurveStrength = float(ReadOptions(FFBClip, FFBClipPath, "Options", "responsecurvestrength", "0.35"))
	AntiFatigueLowBand = float(ReadOptions(FFBClip, FFBClipPath, "Options", "antifatiguelowband", "0.45"))
	AntiFatigueHighBand = float(ReadOptions(FFBClip, FFBClipPath, "Options", "antifatiguehighband", "0.90"))
	AntiFatigueReduction = float(ReadOptions(FFBClip, FFBClipPath, "Options", "antifatiguereduction", "0.10"))
	DiagRefreshSeconds = float(ReadOptions(FFBClip, FFBClipPath, "Options", "diagrefreshseconds", "1.0"))
	CalibrationState = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "calibrationstate", "0")))
	CalibrationWarmupLaps = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "calibrationwarmuplaps", "1")))
	CalibrationLearnLaps = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "calibrationlearnlaps", "2")))
	CalibrationValidationLaps = int(float(ReadOptions(FFBClip, FFBClipPath, "Options", "calibrationvalidationlaps", "1")))
	SessionReportPath = ReadOptions(FFBClip, FFBClipPath, "Options", "sessionreportpath", "apps/python/FFBClip/Config/ffbclip_session_report.txt")
	ManualOverride=float(ReadOptions(FFBClip,FFBClipPath,"Options","manualoverride","0"))
	DDToggle=float(ReadOptions(FFBClip,FFBClipPath,"Options","ddtoggle","0"))
	DDMappingVersion=int(float(ReadOptions(FFBClip,FFBClipPath,"Options","ddmappingversion","0")))
	SetupHash = _compute_setup_hash()
	AdaptiveMode = int(_clamp(AdaptiveMode,0,2))
	LearnLaps = int(_clamp(LearnLaps,1,20))
	LockPercentile = _clamp(LockPercentile,1,50)
	HybridBand = _clamp(HybridBand,0.05,0.50)
	ac.log("TargetGain:" + str(TargetGain))
	settingsPath = ReadOptions(FFBClip, FFBClipPath, "Options", "path", "")
	if settingsPath=="":
		settingsPath = os.path.expanduser(r"~\Documents\Assetto Corsa\cfg\controls.ini")	
## FFBClip section ends

## Combos.ini section start	
	ac.log("Combos.ini section start")
	if os.path.exists(ComboPath):
		ac.log("Combos.ini found")
		Combo.read(ComboPath)
		ac.log("loaded")
		hasStoredLock = _load_combo_lock()
		if Combo.has_option(TrackID+"_"+TrackConfigID,CarID):
			ac.log("Has section and option")
			CarGain = _migrate_dd_legacy_ratio(float(Combo.get(TrackID+"_"+TrackConfigID,CarID)))
			ComboGain=1
			#AutoMode=0
			errorMessage = "Using stored values as starting point"
			if CarGain>2:
				CarGain=2
			ac.log("Combos cargain:"+str(CarGain))
		else:
			ac.log("Combos.ini or section not found")
			CarGain = 1.0
			AutoMode=1
			ComboGain=0
			errorMessage = "Using default values as starting point"
		if hasStoredLock:
			errorMessage = "Stored lock value loaded for this car/track"
			if AdaptiveMode == 1:
				CarGain = LockValue
	else:
		CarGain=1.0
		AutoMode=1
		errorMessage="Combos.ini created"
		with open('apps/python/FFBClip/Config/Combos.ini', 'w') as configfile:
			Combo.write(configfile)		
	CarGain = _migrate_dd_legacy_ratio(CarGain)
	CarGainCombo=CarGain
	ac.log("Combo loaded")
	

## Combos.ini section ends
	
## Controls.ini section start
	if os.path.exists(settingsPath):
		ac.log("Controls.ini found")
		config.read(settingsPath)
		MainGain = float(config.get("STEER","FF_GAIN"))
		ac.log("MainGain:"+str(MainGain))
	else:
	#	#exists(path) is false then we use the v1.0 value and display it
		ac.log("MainGain not found")
		MainGain = 1.0
		errorMessage = "Controls.ini is missing. Using 100%"	
## Controls.ini section ends	

## Read the GainTarget from the ini file
	CarGainTarget=float(ReadOptions(FFBClip,FFBClipPath,"targetgains",CarID,str(TargetGain)))
	TargetGain = _migrate_dd_legacy_ratio(TargetGain)
	CarGainTarget = _migrate_dd_legacy_ratio(CarGainTarget)
	if AdaptiveMode != 0 and LearningComplete == 1:
		LockValue = _clamp(_migrate_dd_legacy_ratio(LockValue), 0.20, 3.0)
		RollbackGain = LockValue
		RollbackLockValue = LockValue
	_commit_dd_mapping_migration()
	if FeaturePresetManager==1:
		_load_preset_if_needed()

	if ManualOverride==1:
		AutoMode=0
		errorMessage = "Manual override, clipping is NOT prevented"
	else:
		AutoMode=1

	ac.log("Setting up the main window")
	appWindow = ac.newApp("FFBClipX")
	ac.setSize(appWindow,360,300)
	ac.setTitle(appWindow,"")
	ac.setIconPosition(appWindow,0,-9000)
	_style_window()

	MainPageWidgets = []
	OptionsNavWidgets = []
	OptionsDriveWidgets = []
	OptionsAdaptiveWidgets = []
	OptionsProtectionWidgets = []
	OptionsToolsWidgets = []
	OptionsActionWidgets = []

	TitleLabel = ac.addLabel(appWindow,"FFBClipX")
	ac.setPosition(TitleLabel,12,8)
	_style_label(TitleLabel, 15, (0.82, 0.93, 1.0, 1.0))

	ComboLabel = ac.addLabel(appWindow,"")
	ac.setPosition(ComboLabel,82,10)
	_style_label(ComboLabel, 11, (0.90, 0.93, 0.98, 1.0))

	StatusBadgeLabel = ac.addLabel(appWindow,"")
	ac.setPosition(StatusBadgeLabel,250,10)
	_style_label(StatusBadgeLabel, 11, (0.55, 0.90, 0.62, 1.0))

	StrengthLabel = ac.addLabel(appWindow,"FFB Strength")
	ac.setPosition(StrengthLabel,133,30)
	_style_label(StrengthLabel, 12, (0.95, 0.97, 1.0, 1.0))

	targetGainSpinner = ac.addSpinner(appWindow,"")
	ac.setPosition(targetGainSpinner,12,48)
	ac.setSize(targetGainSpinner,336,24)
	ac.setRange(targetGainSpinner,10,120)
	ac.setStep(targetGainSpinner,1)
	ac.addOnValueChangeListener(targetGainSpinner,targetChange)
	_style_spinner(targetGainSpinner)

	messageLabel = ac.addLabel(appWindow,errorMessage)
	ac.setPosition(messageLabel,12,80)
	_style_label(messageLabel, 12, (0.96, 0.96, 0.96, 1.0))

	detailLabel = ac.addLabel(appWindow,"")
	ac.setPosition(detailLabel,12,98)
	_style_label(detailLabel, 10, (0.70, 0.78, 0.86, 1.0))

	summaryLabel = ac.addLabel(appWindow,"")
	ac.setPosition(summaryLabel,12,120)
	_style_label(summaryLabel, 11, (0.84, 0.88, 0.94, 1.0))

	summaryLabel2 = ac.addLabel(appWindow,"")
	ac.setPosition(summaryLabel2,12,138)
	_style_label(summaryLabel2, 10, (0.70, 0.78, 0.86, 1.0))

	graph = ac.addGraph(appWindow,"FFB_Graph")
	ac.setPosition(graph,GraphAreaX,GraphAreaY)
	ac.setSize(graph,GraphAreaW,GraphAreaH)
	ac.setRange(graph,-0.05,2.1,300)
	ac.addSerieToGraph(graph,0,1,0)
	ac.addSerieToGraph(graph,1,0,0)
	ac.addSerieToGraph(graph,1,1,0)
	ac.addSerieToGraph(graph,1,1,1)
	ac.addSerieToGraph(graph,0,0,0)

	AutoModeButton = ac.addButton(appWindow,"Mode: Auto")
	ac.setPosition(AutoModeButton,12,266)
	ac.setSize(AutoModeButton,78,24)
	ac.addOnClickedListener(AutoModeButton,AutoModeButtonChange)
	_style_button(AutoModeButton, AutoMode == 1)

	DynamicButton = ac.addButton(appWindow,"Dynamic: OFF")
	ac.setPosition(DynamicButton,98,266)
	ac.setSize(DynamicButton,78,24)
	ac.addOnClickedListener(DynamicButton,DynamicChange)
	_style_button(DynamicButton, DynamicMode == 1)

	ResetButton = ac.addButton(appWindow,"Reset")
	ac.setPosition(ResetButton,184,266)
	ac.setSize(ResetButton,78,24)
	ac.addOnClickedListener(ResetButton,ResetChange)
	_style_button(ResetButton)

	OptionsButton = ac.addButton(appWindow,"Options")
	ac.setPosition(OptionsButton,270,266)
	ac.setSize(OptionsButton,78,24)
	ac.addOnClickedListener(OptionsButton,OptionsChange)
	_style_button(OptionsButton, False, True)

	gainLabel = ac.addLabel(appWindow,"")
	ac.setPosition(gainLabel,12,120)
	_style_label(gainLabel, 11, (0.84, 0.88, 0.94, 1.0))
	ac.setVisible(gainLabel,0)

	MainPageWidgets = [
		TitleLabel, ComboLabel, StatusBadgeLabel, StrengthLabel, targetGainSpinner,
		messageLabel, detailLabel, summaryLabel, summaryLabel2, graph,
		AutoModeButton, DynamicButton, ResetButton, OptionsButton
	]

	OptionTitleLabel = ac.addLabel(appWindow,"Drive & Session")
	ac.setPosition(OptionTitleLabel,12,12)
	_style_label(OptionTitleLabel, 15, (0.98, 0.99, 1.0, 1.0))

	OptionHintLabel = ac.addLabel(appWindow,"Advanced controls are split by topic to keep the live HUD clean.")
	ac.setPosition(OptionHintLabel,12,32)
	_style_label(OptionHintLabel, 11, (0.82, 0.87, 0.93, 1.0))

	DriveTabButton = ac.addButton(appWindow,"Drive")
	ac.setPosition(DriveTabButton,12,54)
	ac.setSize(DriveTabButton,104,24)
	ac.addOnClickedListener(DriveTabButton,OptionsTabDriveChange)

	AdaptiveTabButton = ac.addButton(appWindow,"Adaptive")
	ac.setPosition(AdaptiveTabButton,122,54)
	ac.setSize(AdaptiveTabButton,104,24)
	ac.addOnClickedListener(AdaptiveTabButton,OptionsTabAdaptiveChange)

	ProtectionTabButton = ac.addButton(appWindow,"Protection")
	ac.setPosition(ProtectionTabButton,232,54)
	ac.setSize(ProtectionTabButton,104,24)
	ac.addOnClickedListener(ProtectionTabButton,OptionsTabProtectionChange)

	ToolsTabButton = ac.addButton(appWindow,"Tools")
	ac.setPosition(ToolsTabButton,342,54)
	ac.setSize(ToolsTabButton,106,24)
	ac.addOnClickedListener(ToolsTabButton,OptionsTabToolsChange)

	OptionsNavWidgets = [OptionTitleLabel, OptionHintLabel, DriveTabButton, AdaptiveTabButton, ProtectionTabButton, ToolsTabButton]

	ManualToggle = ac.addCheckBox(appWindow,"Manual override")
	ac.setPosition(ManualToggle,20,92)
	ac.setSize(ManualToggle,10,10)
	ac.setValue(ManualToggle,1 if AutoMode == 0 else 0)
	ac.addOnCheckBoxChanged(ManualToggle,ManualToggleChange)
	_style_checkbox(ManualToggle)

	DDToggleButton = ac.addCheckBox(appWindow,"Direct Drive mode")
	ac.setPosition(DDToggleButton,240,92)
	ac.setSize(DDToggleButton,10,10)
	ac.setValue(DDToggleButton,DDToggle)
	ac.addOnCheckBoxChanged(DDToggleButton,DDToggleButtonChange)
	_style_checkbox(DDToggleButton)

	RBToggle = ac.addCheckBox(appWindow,"Run in background")
	ac.setPosition(RBToggle,20,118)
	ac.setSize(RBToggle,10,10)
	ac.setValue(RBToggle,RB)
	ac.addOnCheckBoxChanged(RBToggle,RBToggleChange)
	_style_checkbox(RBToggle)

	FeatureCSVToggle = ac.addCheckBox(appWindow,"CSV logging")
	ac.setPosition(FeatureCSVToggle,240,118)
	ac.setSize(FeatureCSVToggle,10,10)
	ac.setValue(FeatureCSVToggle,FeatureCSVLogging)
	ac.addOnCheckBoxChanged(FeatureCSVToggle,FeatureCSVToggleChange)
	_style_checkbox(FeatureCSVToggle)

	DefaultgainSpinnerLabel = ac.addLabel(appWindow,"Default FFB strength (%)")
	ac.setPosition(DefaultgainSpinnerLabel,20,152)
	_style_label(DefaultgainSpinnerLabel, 11, (0.92, 0.94, 0.98, 1.0))

	DefaultGainSpinner = ac.addSpinner(appWindow,"")
	ac.setPosition(DefaultGainSpinner,20,170)
	ac.setSize(DefaultGainSpinner,190,24)
	ac.setRange(DefaultGainSpinner,10,120)
	ac.setStep(DefaultGainSpinner,1)
	ac.addOnValueChangeListener(DefaultGainSpinner,DefaultGainChange)
	_style_spinner(DefaultGainSpinner)

	TorqueSpinner = ac.addSpinner(appWindow,"Hardware max torque")
	ac.setPosition(TorqueSpinner,240,170)
	ac.setSize(TorqueSpinner,190,24)
	ac.setRange(TorqueSpinner,3,50)
	ac.setStep(TorqueSpinner,1)
	ac.setValue(TorqueSpinner,MaxTorque)
	ac.addOnValueChangeListener(TorqueSpinner,TorqueChange)
	_style_spinner(TorqueSpinner)

	DisplaymodeButtonLabel = ac.addLabel(appWindow,"Display mode")
	ac.setPosition(DisplaymodeButtonLabel,20,208)
	_style_label(DisplaymodeButtonLabel, 11, (0.92, 0.94, 0.98, 1.0))

	DisplaymodeButton = ac.addButton(appWindow,"Off")
	ac.setPosition(DisplaymodeButton,20,226)
	ac.setSize(DisplaymodeButton,190,22)
	ac.addOnClickedListener(DisplaymodeButton,DisplaymodeButtonChange)
	_style_button(DisplaymodeButton, False, True)

	GraphRefreshSpinner = ac.addSpinner(appWindow,"Graph refresh (Hz)")
	ac.setPosition(GraphRefreshSpinner,240,226)
	ac.setSize(GraphRefreshSpinner,190,24)
	ac.setRange(GraphRefreshSpinner,1,30)
	ac.setStep(GraphRefreshSpinner,1)
	ac.setValue(GraphRefreshSpinner,GraphRefresh)
	ac.addOnValueChangeListener(GraphRefreshSpinner,GraphRefreshChange)
	_style_spinner(GraphRefreshSpinner)

	DynamicThresholdSpinner = ac.addSpinner(appWindow,"Dynamic threshold (%)")
	ac.setPosition(DynamicThresholdSpinner,20,274)
	ac.setSize(DynamicThresholdSpinner,190,24)
	ac.setRange(DynamicThresholdSpinner,10,300)
	ac.setStep(DynamicThresholdSpinner,10)
	ac.setValue(DynamicThresholdSpinner,DynamicThreshold*100)
	ac.addOnValueChangeListener(DynamicThresholdSpinner,DynamicThresholdSpinnerChange)
	_style_spinner(DynamicThresholdSpinner)

	DynamicSpeedSpinner = ac.addSpinner(appWindow,"Dynamic intensity")
	ac.setPosition(DynamicSpeedSpinner,240,274)
	ac.setSize(DynamicSpeedSpinner,190,24)
	ac.setRange(DynamicSpeedSpinner,50,500)
	ac.setStep(DynamicSpeedSpinner,10)
	ac.setValue(DynamicSpeedSpinner,DynamicSpeed*10000)
	ac.addOnValueChangeListener(DynamicSpeedSpinner,DynamicSpeedSpinnerChange)
	_style_spinner(DynamicSpeedSpinner)

	FeaturePresetToggle = ac.addCheckBox(appWindow,"Preset snapshot")
	ac.setPosition(FeaturePresetToggle,20,318)
	ac.setSize(FeaturePresetToggle,10,10)
	ac.setValue(FeaturePresetToggle,FeaturePresetManager)
	ac.addOnCheckBoxChanged(FeaturePresetToggle,FeaturePresetToggleChange)
	_style_checkbox(FeaturePresetToggle)

	FeatureReportToggle = ac.addCheckBox(appWindow,"Session report")
	ac.setPosition(FeatureReportToggle,240,318)
	ac.setSize(FeatureReportToggle,10,10)
	ac.setValue(FeatureReportToggle,FeatureSessionReport)
	ac.addOnCheckBoxChanged(FeatureReportToggle,FeatureReportToggleChange)
	_style_checkbox(FeatureReportToggle)

	OptionsDriveWidgets = [
		ManualToggle, DDToggleButton, RBToggle, FeatureCSVToggle,
		DefaultgainSpinnerLabel, DefaultGainSpinner, TorqueSpinner,
		DisplaymodeButtonLabel, DisplaymodeButton, GraphRefreshSpinner,
		DynamicThresholdSpinner, DynamicSpeedSpinner, FeaturePresetToggle, FeatureReportToggle
	]

	AdaptiveModeLabel = ac.addLabel(appWindow,"Adaptive mode")
	ac.setPosition(AdaptiveModeLabel,20,92)
	_style_label(AdaptiveModeLabel, 11, (0.92, 0.94, 0.98, 1.0))

	AdaptiveModeButton = ac.addButton(appWindow,"Classic")
	ac.setPosition(AdaptiveModeButton,20,110)
	ac.setSize(AdaptiveModeButton,190,22)
	ac.addOnClickedListener(AdaptiveModeButton,AdaptiveModeButtonChange)
	_style_button(AdaptiveModeButton, False, True)

	ProfileModeLabel = ac.addLabel(appWindow,"Profile mode")
	ac.setPosition(ProfileModeLabel,240,92)
	_style_label(ProfileModeLabel, 11, (0.92, 0.94, 0.98, 1.0))

	ProfileModeButton = ac.addButton(appWindow,"Race")
	ac.setPosition(ProfileModeButton,240,110)
	ac.setSize(ProfileModeButton,190,22)
	ac.addOnClickedListener(ProfileModeButton,ProfileModeButtonChange)
	_style_button(ProfileModeButton, False, True)

	LearnLapsSpinner = ac.addSpinner(appWindow,"Learn laps")
	ac.setPosition(LearnLapsSpinner,20,158)
	ac.setSize(LearnLapsSpinner,190,24)
	ac.setRange(LearnLapsSpinner,1,20)
	ac.setStep(LearnLapsSpinner,1)
	ac.setValue(LearnLapsSpinner,LearnLaps)
	ac.addOnValueChangeListener(LearnLapsSpinner,LearnLapsSpinnerChange)
	_style_spinner(LearnLapsSpinner)

	LockPercentileSpinner = ac.addSpinner(appWindow,"Lock percentile")
	ac.setPosition(LockPercentileSpinner,240,158)
	ac.setSize(LockPercentileSpinner,190,24)
	ac.setRange(LockPercentileSpinner,1,50)
	ac.setStep(LockPercentileSpinner,1)
	ac.setValue(LockPercentileSpinner,LockPercentile)
	ac.addOnValueChangeListener(LockPercentileSpinner,LockPercentileSpinnerChange)
	_style_spinner(LockPercentileSpinner)

	HybridBandSpinner = ac.addSpinner(appWindow,"Hybrid band (%)")
	ac.setPosition(HybridBandSpinner,20,206)
	ac.setSize(HybridBandSpinner,190,24)
	ac.setRange(HybridBandSpinner,5,50)
	ac.setStep(HybridBandSpinner,1)
	ac.setValue(HybridBandSpinner,HybridBand*100)
	ac.addOnValueChangeListener(HybridBandSpinner,HybridBandSpinnerChange)
	_style_spinner(HybridBandSpinner)

	ConfidenceGateSpinner = ac.addSpinner(appWindow,"Confidence gate (%)")
	ac.setPosition(ConfidenceGateSpinner,240,206)
	ac.setSize(ConfidenceGateSpinner,190,24)
	ac.setRange(ConfidenceGateSpinner,50,98)
	ac.setStep(ConfidenceGateSpinner,1)
	ac.setValue(ConfidenceGateSpinner,ConfidenceGateThreshold*100)
	ac.addOnValueChangeListener(ConfidenceGateSpinner,ConfidenceGateSpinnerChange)
	_style_spinner(ConfidenceGateSpinner)

	FeaturePhaseToggle = ac.addCheckBox(appWindow,"Phase learning")
	ac.setPosition(FeaturePhaseToggle,20,252)
	ac.setSize(FeaturePhaseToggle,10,10)
	ac.setValue(FeaturePhaseToggle,FeaturePhaseLearning)
	ac.addOnCheckBoxChanged(FeaturePhaseToggle,FeaturePhaseToggleChange)
	_style_checkbox(FeaturePhaseToggle)

	FeatureLearningToggle = ac.addCheckBox(appWindow,"Show confidence")
	ac.setPosition(FeatureLearningToggle,240,252)
	ac.setSize(FeatureLearningToggle,10,10)
	ac.setValue(FeatureLearningToggle,FeatureLearningConfidence)
	ac.addOnCheckBoxChanged(FeatureLearningToggle,FeatureLearningToggleChange)
	_style_checkbox(FeatureLearningToggle)

	FeatureConfidenceToggle = ac.addCheckBox(appWindow,"Confidence gate")
	ac.setPosition(FeatureConfidenceToggle,20,278)
	ac.setSize(FeatureConfidenceToggle,10,10)
	ac.setValue(FeatureConfidenceToggle,FeatureConfidenceGate)
	ac.addOnCheckBoxChanged(FeatureConfidenceToggle,FeatureConfidenceToggleChange)
	_style_checkbox(FeatureConfidenceToggle)

	FeatureSetupToggle = ac.addCheckBox(appWindow,"Setup-aware learn")
	ac.setPosition(FeatureSetupToggle,240,278)
	ac.setSize(FeatureSetupToggle,10,10)
	ac.setValue(FeatureSetupToggle,FeatureSetupAwareLearning)
	ac.addOnCheckBoxChanged(FeatureSetupToggle,FeatureSetupToggleChange)
	_style_checkbox(FeatureSetupToggle)

	FeatureAutoResetToggle = ac.addCheckBox(appWindow,"Auto reset combo")
	ac.setPosition(FeatureAutoResetToggle,20,304)
	ac.setSize(FeatureAutoResetToggle,10,10)
	ac.setValue(FeatureAutoResetToggle,FeatureAutoResetCombo)
	ac.addOnCheckBoxChanged(FeatureAutoResetToggle,FeatureAutoResetToggleChange)
	_style_checkbox(FeatureAutoResetToggle)

	AutoProfileToggle = ac.addCheckBox(appWindow,"Auto session profile")
	ac.setPosition(AutoProfileToggle,240,304)
	ac.setSize(AutoProfileToggle,10,10)
	ac.setValue(AutoProfileToggle,AutoProfileSession)
	ac.addOnCheckBoxChanged(AutoProfileToggle,AutoProfileToggleChange)
	_style_checkbox(AutoProfileToggle)

	FeatureProfileToggle = ac.addCheckBox(appWindow,"Profile shaping")
	ac.setPosition(FeatureProfileToggle,20,330)
	ac.setSize(FeatureProfileToggle,10,10)
	ac.setValue(FeatureProfileToggle,FeatureProfileMode)
	ac.addOnCheckBoxChanged(FeatureProfileToggle,FeatureProfileToggleChange)
	_style_checkbox(FeatureProfileToggle)

	FeatureRollbackToggle = ac.addCheckBox(appWindow,"Rollback gate")
	ac.setPosition(FeatureRollbackToggle,240,330)
	ac.setSize(FeatureRollbackToggle,10,10)
	ac.setValue(FeatureRollbackToggle,FeatureRollbackOneClick)
	ac.addOnCheckBoxChanged(FeatureRollbackToggle,FeatureRollbackToggleChange)
	_style_checkbox(FeatureRollbackToggle)

	OptionsAdaptiveWidgets = [
		AdaptiveModeLabel, AdaptiveModeButton, ProfileModeLabel, ProfileModeButton,
		LearnLapsSpinner, LockPercentileSpinner, HybridBandSpinner, ConfidenceGateSpinner,
		FeaturePhaseToggle, FeatureLearningToggle, FeatureConfidenceToggle, FeatureSetupToggle,
		FeatureAutoResetToggle, AutoProfileToggle, FeatureProfileToggle, FeatureRollbackToggle
	]

	FeatureOutlierToggle = ac.addCheckBox(appWindow,"Outlier filter")
	ac.setPosition(FeatureOutlierToggle,20,92)
	ac.setSize(FeatureOutlierToggle,10,10)
	ac.setValue(FeatureOutlierToggle,FeatureOutlierFilter)
	ac.addOnCheckBoxChanged(FeatureOutlierToggle,FeatureOutlierToggleChange)
	_style_checkbox(FeatureOutlierToggle)

	FeatureOscillationToggle = ac.addCheckBox(appWindow,"Anti oscillation")
	ac.setPosition(FeatureOscillationToggle,240,92)
	ac.setSize(FeatureOscillationToggle,10,10)
	ac.setValue(FeatureOscillationToggle,FeatureAntiOscillation)
	ac.addOnCheckBoxChanged(FeatureOscillationToggle,FeatureOscillationToggleChange)
	_style_checkbox(FeatureOscillationToggle)

	FeatureSafetyToggle = ac.addCheckBox(appWindow,"Safety limits")
	ac.setPosition(FeatureSafetyToggle,20,118)
	ac.setSize(FeatureSafetyToggle,10,10)
	ac.setValue(FeatureSafetyToggle,FeatureSafetyLimits)
	ac.addOnCheckBoxChanged(FeatureSafetyToggle,FeatureSafetyToggleChange)
	_style_checkbox(FeatureSafetyToggle)

	FeatureEnduranceToggle = ac.addCheckBox(appWindow,"Endurance ceiling")
	ac.setPosition(FeatureEnduranceToggle,240,118)
	ac.setSize(FeatureEnduranceToggle,10,10)
	ac.setValue(FeatureEnduranceToggle,FeatureEnduranceMode)
	ac.addOnCheckBoxChanged(FeatureEnduranceToggle,FeatureEnduranceToggleChange)
	_style_checkbox(FeatureEnduranceToggle)

	SafetyFloorSpinner = ac.addSpinner(appWindow,"Safety floor (%)")
	ac.setPosition(SafetyFloorSpinner,20,158)
	ac.setSize(SafetyFloorSpinner,190,24)
	ac.setRange(SafetyFloorSpinner,20,150)
	ac.setStep(SafetyFloorSpinner,5)
	ac.setValue(SafetyFloorSpinner,SafetyFloor*100)
	ac.addOnValueChangeListener(SafetyFloorSpinner,SafetyFloorSpinnerChange)
	_style_spinner(SafetyFloorSpinner)

	SafetyCeilingSpinner = ac.addSpinner(appWindow,"Safety ceiling (%)")
	ac.setPosition(SafetyCeilingSpinner,240,158)
	ac.setSize(SafetyCeilingSpinner,190,24)
	ac.setRange(SafetyCeilingSpinner,80,300)
	ac.setStep(SafetyCeilingSpinner,5)
	ac.setValue(SafetyCeilingSpinner,SafetyCeiling*100)
	ac.addOnValueChangeListener(SafetyCeilingSpinner,SafetyCeilingSpinnerChange)
	_style_spinner(SafetyCeilingSpinner)

	OscillationDeadbandSpinner = ac.addSpinner(appWindow,"Deadband (%)")
	ac.setPosition(OscillationDeadbandSpinner,20,206)
	ac.setSize(OscillationDeadbandSpinner,190,24)
	ac.setRange(OscillationDeadbandSpinner,0,20)
	ac.setStep(OscillationDeadbandSpinner,1)
	ac.setValue(OscillationDeadbandSpinner,OscillationDeadband*100)
	ac.addOnValueChangeListener(OscillationDeadbandSpinner,OscillationDeadbandSpinnerChange)
	_style_spinner(OscillationDeadbandSpinner)

	OscillationMinIntervalSpinner = ac.addSpinner(appWindow,"Min interval (ms)")
	ac.setPosition(OscillationMinIntervalSpinner,240,206)
	ac.setSize(OscillationMinIntervalSpinner,190,24)
	ac.setRange(OscillationMinIntervalSpinner,50,1000)
	ac.setStep(OscillationMinIntervalSpinner,10)
	ac.setValue(OscillationMinIntervalSpinner,OscillationMinInterval*1000)
	ac.addOnValueChangeListener(OscillationMinIntervalSpinner,OscillationMinIntervalSpinnerChange)
	_style_spinner(OscillationMinIntervalSpinner)

	EnduranceMinutesSpinner = ac.addSpinner(appWindow,"Endurance start (min)")
	ac.setPosition(EnduranceMinutesSpinner,20,254)
	ac.setSize(EnduranceMinutesSpinner,190,24)
	ac.setRange(EnduranceMinutesSpinner,10,240)
	ac.setStep(EnduranceMinutesSpinner,5)
	ac.setValue(EnduranceMinutesSpinner,EnduranceMinutes)
	ac.addOnValueChangeListener(EnduranceMinutesSpinner,EnduranceMinutesSpinnerChange)
	_style_spinner(EnduranceMinutesSpinner)

	EnduranceDropSpinner = ac.addSpinner(appWindow,"Max endurance drop (%)")
	ac.setPosition(EnduranceDropSpinner,240,254)
	ac.setSize(EnduranceDropSpinner,190,24)
	ac.setRange(EnduranceDropSpinner,0,30)
	ac.setStep(EnduranceDropSpinner,1)
	ac.setValue(EnduranceDropSpinner,EnduranceDropMax*100)
	ac.addOnValueChangeListener(EnduranceDropSpinner,EnduranceDropSpinnerChange)
	_style_spinner(EnduranceDropSpinner)

	FeatureWetToggle = ac.addCheckBox(appWindow,"Wet softening")
	ac.setPosition(FeatureWetToggle,20,302)
	ac.setSize(FeatureWetToggle,10,10)
	ac.setValue(FeatureWetToggle,FeatureWetMode)
	ac.addOnCheckBoxChanged(FeatureWetToggle,FeatureWetToggleChange)
	_style_checkbox(FeatureWetToggle)

	FeatureKerbToggle = ac.addCheckBox(appWindow,"Kerb filter")
	ac.setPosition(FeatureKerbToggle,240,302)
	ac.setSize(FeatureKerbToggle,10,10)
	ac.setValue(FeatureKerbToggle,FeatureKerbFilter)
	ac.addOnCheckBoxChanged(FeatureKerbToggle,FeatureKerbToggleChange)
	_style_checkbox(FeatureKerbToggle)

	WetGripSpinner = ac.addSpinner(appWindow,"Wet grip threshold (%)")
	ac.setPosition(WetGripSpinner,20,338)
	ac.setSize(WetGripSpinner,190,24)
	ac.setRange(WetGripSpinner,60,100)
	ac.setStep(WetGripSpinner,1)
	ac.setValue(WetGripSpinner,WetGripThreshold*100)
	ac.addOnValueChangeListener(WetGripSpinner,WetGripSpinnerChange)
	_style_spinner(WetGripSpinner)

	WetSofteningSpinner = ac.addSpinner(appWindow,"Wet softening (%)")
	ac.setPosition(WetSofteningSpinner,240,338)
	ac.setSize(WetSofteningSpinner,190,24)
	ac.setRange(WetSofteningSpinner,0,30)
	ac.setStep(WetSofteningSpinner,1)
	ac.setValue(WetSofteningSpinner,WetSoftening*100)
	ac.addOnValueChangeListener(WetSofteningSpinner,WetSofteningSpinnerChange)
	_style_spinner(WetSofteningSpinner)

	KerbSpikeSpinner = ac.addSpinner(appWindow,"Kerb spike threshold (%)")
	ac.setPosition(KerbSpikeSpinner,20,386)
	ac.setSize(KerbSpikeSpinner,190,24)
	ac.setRange(KerbSpikeSpinner,5,80)
	ac.setStep(KerbSpikeSpinner,1)
	ac.setValue(KerbSpikeSpinner,KerbSpikeThreshold*100)
	ac.addOnValueChangeListener(KerbSpikeSpinner,KerbSpikeSpinnerChange)
	_style_spinner(KerbSpikeSpinner)

	KerbDampSpinner = ac.addSpinner(appWindow,"Kerb damp factor (%)")
	ac.setPosition(KerbDampSpinner,240,386)
	ac.setSize(KerbDampSpinner,190,24)
	ac.setRange(KerbDampSpinner,35,100)
	ac.setStep(KerbDampSpinner,1)
	ac.setValue(KerbDampSpinner,KerbDampFactor*100)
	ac.addOnValueChangeListener(KerbDampSpinner,KerbDampSpinnerChange)
	_style_spinner(KerbDampSpinner)

	OptionsProtectionWidgets = [
		FeatureOutlierToggle, FeatureOscillationToggle, FeatureSafetyToggle, FeatureEnduranceToggle,
		SafetyFloorSpinner, SafetyCeilingSpinner, OscillationDeadbandSpinner, OscillationMinIntervalSpinner,
		EnduranceMinutesSpinner, EnduranceDropSpinner, FeatureWetToggle, FeatureKerbToggle,
		WetGripSpinner, WetSofteningSpinner, KerbSpikeSpinner, KerbDampSpinner
	]

	FeatureCurveToggle = ac.addCheckBox(appWindow,"Response curves")
	ac.setPosition(FeatureCurveToggle,20,92)
	ac.setSize(FeatureCurveToggle,10,10)
	ac.setValue(FeatureCurveToggle,FeatureResponseCurves)
	ac.addOnCheckBoxChanged(FeatureCurveToggle,FeatureCurveToggleChange)
	_style_checkbox(FeatureCurveToggle)

	FeatureFatigueToggle = ac.addCheckBox(appWindow,"Anti fatigue")
	ac.setPosition(FeatureFatigueToggle,240,92)
	ac.setSize(FeatureFatigueToggle,10,10)
	ac.setValue(FeatureFatigueToggle,FeatureAdvancedAntiFatigue)
	ac.addOnCheckBoxChanged(FeatureFatigueToggle,FeatureFatigueToggleChange)
	_style_checkbox(FeatureFatigueToggle)

	ResponseCurveModeLabel = ac.addLabel(appWindow,"Response curve")
	ac.setPosition(ResponseCurveModeLabel,20,124)
	_style_label(ResponseCurveModeLabel, 11, (0.92, 0.94, 0.98, 1.0))

	ResponseCurveModeButton = ac.addButton(appWindow,"Linear")
	ac.setPosition(ResponseCurveModeButton,20,142)
	ac.setSize(ResponseCurveModeButton,190,22)
	ac.addOnClickedListener(ResponseCurveModeButton,ResponseCurveModeButtonChange)
	_style_button(ResponseCurveModeButton, False, True)

	ResponseCurveStrengthSpinner = ac.addSpinner(appWindow,"Curve strength (%)")
	ac.setPosition(ResponseCurveStrengthSpinner,240,142)
	ac.setSize(ResponseCurveStrengthSpinner,190,24)
	ac.setRange(ResponseCurveStrengthSpinner,0,100)
	ac.setStep(ResponseCurveStrengthSpinner,1)
	ac.setValue(ResponseCurveStrengthSpinner,ResponseCurveStrength*100)
	ac.addOnValueChangeListener(ResponseCurveStrengthSpinner,ResponseCurveStrengthSpinnerChange)
	_style_spinner(ResponseCurveStrengthSpinner)

	AntiFatigueLowSpinner = ac.addSpinner(appWindow,"Fatigue low band (%)")
	ac.setPosition(AntiFatigueLowSpinner,20,190)
	ac.setSize(AntiFatigueLowSpinner,190,24)
	ac.setRange(AntiFatigueLowSpinner,20,90)
	ac.setStep(AntiFatigueLowSpinner,1)
	ac.setValue(AntiFatigueLowSpinner,AntiFatigueLowBand*100)
	ac.addOnValueChangeListener(AntiFatigueLowSpinner,AntiFatigueLowSpinnerChange)
	_style_spinner(AntiFatigueLowSpinner)

	AntiFatigueHighSpinner = ac.addSpinner(appWindow,"Fatigue high band (%)")
	ac.setPosition(AntiFatigueHighSpinner,240,190)
	ac.setSize(AntiFatigueHighSpinner,190,24)
	ac.setRange(AntiFatigueHighSpinner,30,100)
	ac.setStep(AntiFatigueHighSpinner,1)
	ac.setValue(AntiFatigueHighSpinner,AntiFatigueHighBand*100)
	ac.addOnValueChangeListener(AntiFatigueHighSpinner,AntiFatigueHighSpinnerChange)
	_style_spinner(AntiFatigueHighSpinner)

	AntiFatigueReductionSpinner = ac.addSpinner(appWindow,"Fatigue reduction (%)")
	ac.setPosition(AntiFatigueReductionSpinner,20,238)
	ac.setSize(AntiFatigueReductionSpinner,190,24)
	ac.setRange(AntiFatigueReductionSpinner,0,35)
	ac.setStep(AntiFatigueReductionSpinner,1)
	ac.setValue(AntiFatigueReductionSpinner,AntiFatigueReduction*100)
	ac.addOnValueChangeListener(AntiFatigueReductionSpinner,AntiFatigueReductionSpinnerChange)
	_style_spinner(AntiFatigueReductionSpinner)

	FeatureDiagToggle = ac.addCheckBox(appWindow,"Diag dashboard")
	ac.setPosition(FeatureDiagToggle,240,238)
	ac.setSize(FeatureDiagToggle,10,10)
	ac.setValue(FeatureDiagToggle,FeatureDiagnosticDashboard)
	ac.addOnCheckBoxChanged(FeatureDiagToggle,FeatureDiagToggleChange)
	_style_checkbox(FeatureDiagToggle)

	DiagRefreshSpinner = ac.addSpinner(appWindow,"Diag refresh (s x100)")
	ac.setPosition(DiagRefreshSpinner,20,286)
	ac.setSize(DiagRefreshSpinner,190,24)
	ac.setRange(DiagRefreshSpinner,25,500)
	ac.setStep(DiagRefreshSpinner,5)
	ac.setValue(DiagRefreshSpinner,DiagRefreshSeconds*100)
	ac.addOnValueChangeListener(DiagRefreshSpinner,DiagRefreshSpinnerChange)
	_style_spinner(DiagRefreshSpinner)

	FeatureCalibToggle = ac.addCheckBox(appWindow,"Calibration helper")
	ac.setPosition(FeatureCalibToggle,240,286)
	ac.setSize(FeatureCalibToggle,10,10)
	ac.setValue(FeatureCalibToggle,FeatureCalibrationAssistant)
	ac.addOnCheckBoxChanged(FeatureCalibToggle,FeatureCalibToggleChange)
	_style_checkbox(FeatureCalibToggle)

	CalibrationWarmupSpinner = ac.addSpinner(appWindow,"Calib warmup laps")
	ac.setPosition(CalibrationWarmupSpinner,20,334)
	ac.setSize(CalibrationWarmupSpinner,190,24)
	ac.setRange(CalibrationWarmupSpinner,0,5)
	ac.setStep(CalibrationWarmupSpinner,1)
	ac.setValue(CalibrationWarmupSpinner,CalibrationWarmupLaps)
	ac.addOnValueChangeListener(CalibrationWarmupSpinner,CalibrationWarmupSpinnerChange)
	_style_spinner(CalibrationWarmupSpinner)

	CalibrationLearnSpinner = ac.addSpinner(appWindow,"Calib learn laps")
	ac.setPosition(CalibrationLearnSpinner,240,334)
	ac.setSize(CalibrationLearnSpinner,190,24)
	ac.setRange(CalibrationLearnSpinner,1,10)
	ac.setStep(CalibrationLearnSpinner,1)
	ac.setValue(CalibrationLearnSpinner,CalibrationLearnLaps)
	ac.addOnValueChangeListener(CalibrationLearnSpinner,CalibrationLearnSpinnerChange)
	_style_spinner(CalibrationLearnSpinner)

	CalibrationValidationSpinner = ac.addSpinner(appWindow,"Calib validation laps")
	ac.setPosition(CalibrationValidationSpinner,20,382)
	ac.setSize(CalibrationValidationSpinner,190,24)
	ac.setRange(CalibrationValidationSpinner,1,10)
	ac.setStep(CalibrationValidationSpinner,1)
	ac.setValue(CalibrationValidationSpinner,CalibrationValidationLaps)
	ac.addOnValueChangeListener(CalibrationValidationSpinner,CalibrationValidationSpinnerChange)
	_style_spinner(CalibrationValidationSpinner)

	OptionsToolsWidgets = [
		FeatureCurveToggle, FeatureFatigueToggle, ResponseCurveModeLabel, ResponseCurveModeButton,
		ResponseCurveStrengthSpinner, AntiFatigueLowSpinner, AntiFatigueHighSpinner, AntiFatigueReductionSpinner,
		FeatureDiagToggle, DiagRefreshSpinner, FeatureCalibToggle, CalibrationWarmupSpinner,
		CalibrationLearnSpinner, CalibrationValidationSpinner
	]

	CalibrationButton = ac.addButton(appWindow,"Start calib")
	ac.setPosition(CalibrationButton,12,434)
	ac.setSize(CalibrationButton,100,24)
	ac.addOnClickedListener(CalibrationButton,CalibrationButtonChange)
	_style_button(CalibrationButton)

	ResetLearningButton = ac.addButton(appWindow,"Reset learn")
	ac.setPosition(ResetLearningButton,122,434)
	ac.setSize(ResetLearningButton,100,24)
	ac.addOnClickedListener(ResetLearningButton,ResetLearningButtonChange)
	_style_button(ResetLearningButton)

	RollbackButton = ac.addButton(appWindow,"Rollback")
	ac.setPosition(RollbackButton,232,434)
	ac.setSize(RollbackButton,100,24)
	ac.addOnClickedListener(RollbackButton,RollbackButtonChange)
	_style_button(RollbackButton)

	OptionsActionWidgets = [CalibrationButton, ResetLearningButton, RollbackButton, OptionsButton]

	_sync_gain_controls()
	_refresh_ui_text()
	_set_options_page(False)
	ac.addRenderCallback(appWindow,onFormRender)
	ac.console("FFBClip successful")
	return "FFBClipX"
	
def acUpdate(deltaT):

	global OldRAW,Histogram,MainGain,CarGain,CarGainCombo,CurrentForce,i,RB,dT,RuntimeMinutesEstimate,PeakForceWindow,GraphPeakForceWindow

## Runs every tick
	CurrentForce = abs(ac.getCarState(0,acsys.CS.LastFF))
	PeakForceWindow = max(PeakForceWindow, CurrentForce)
	GraphPeakForceWindow = max(GraphPeakForceWindow, CurrentForce)

	n=int(CurrentForce*200)
	n=int(_clamp(n,1,299))
	if n>0 and OldRAW != CurrentForce:
		a=Histogram.pop(n)
		if n<(50*MainGain):
			inc=n/(50*MainGain)
		else:
			inc=1	
		a += inc
		Histogram.insert(n,a)
		#ac.console(str(n) + " - " + str(a))
	OldRAW=CurrentForce
	
	if RB == 1:
		dT += deltaT
		RuntimeMinutesEstimate += (deltaT/60.0)
		RunAll(deltaT)

def onFormRender(deltaT):
	
	global Version,appWindow
	global messageLabel,gainLabel
	global errorMessage,graph
	global CarGainTarget,ffbMultiplier,Histogram,dT,CarGain,OldCarGain,CurrentForce,OldFFBMultiplier
	global AutoMode,OldGain,Cutoff, DynamicMode, TargetGain,DynamicTarget,MainGain,OldRAW,ffbMultiplierSmooth,ffbMultiplierSmoothOld
	global DynamicThreshold,DynamicSpeed,DynamicAdd,dTG,GraphRefresh,i,RB,RuntimeMinutesEstimate,GraphPeakForceWindow
	
	dTG += deltaT
	if RB != 1:
		dT += deltaT
		RuntimeMinutesEstimate += (deltaT/60.0)
		RunAll(deltaT)
	
	if DisplayMode == 1 and dTG > (1/GraphRefresh):
		_push_graph_sample(max(CurrentForce, GraphPeakForceWindow), CarGainTarget)
		GraphPeakForceWindow = 0.0
		dTG=0

	if OptionsPage == 0 and DisplayMode == 1:
		_draw_realtime_graph()
		
	if DisplayMode == 2 and dTG > 1:
		HMax = max(Histogram)+1
		n=i
		for i in range(0,300):
			ac.addValueToGraph(graph,0,(Histogram[i]/HMax))
			if i<200:
				ac.addValueToGraph(graph,2,0)
			else:
				ac.addValueToGraph(graph,2,1)
				#ac.addValueToGraph(graph,1,Cutoff)
				#if i>n:
				#	ac.addValueToGraph(graph,3,1)
				#else:
				#	ac.addValueToGraph(graph,3,0)
				#if i>(CarGainTarget*200):
				#	ac.addValueToGraph(graph,4,1)
				#else:
				#	ac.addValueToGraph(graph,4,0)
		dTG=0	
		
			
def acShutdown(*args):

	global TrackID,TrackConfigID,CarID,CarGain,config,Combo,ComboPath,CurrentProfile,FFBClip,FFBClipPath,ManualOverride,MaxTorque,TargetGain
	global DDToggle,GraphRefresh,DisplayMode,DynamicThreshold,DynamicSpeed,RB,DDMappingVersion
	global AdaptiveMode,LearningComplete,LockValue
	global FeatureWetMode,FeatureKerbFilter,FeatureSetupAwareLearning,FeatureConfidenceGate,FeatureRollbackOneClick,FeatureResponseCurves,FeatureAdvancedAntiFatigue,FeatureDiagnosticDashboard,FeatureCalibrationAssistant,FeatureSessionReport
	global WetGripThreshold,WetSoftening,KerbSpikeThreshold,KerbDampFactor,SetupHash,ConfidenceGateThreshold,RollbackGain,RollbackLockValue,ResponseCurveMode,ResponseCurveStrength,AntiFatigueLowBand,AntiFatigueHighBand,AntiFatigueReduction,DiagRefreshSeconds,CalibrationState,CalibrationWarmupLaps,CalibrationLearnLaps,CalibrationValidationLaps,SessionReportPath

	
	ac.log("shutdown")
	current_shutdown_gain = round(ac.getCarFFB()/100.0, 2)
	
	if os.path.exists(ComboPath):
		if Combo.has_section(TrackID+"_"+TrackConfigID):
			ac.log("found track")
			if Combo.has_option(TrackID+"_"+TrackConfigID,CarID):
				ac.log("Car found")
				Combo.remove_option(TrackID+"_"+TrackConfigID,CarID)
				Combo.set(TrackID+"_"+TrackConfigID,CarID,str(current_shutdown_gain))
			else:
				ac.log("Car not found")
				Combo.set(TrackID+"_"+TrackConfigID,CarID,str(current_shutdown_gain))
				ac.log("add")
		else:
			ac.log("Track not found")
			Combo.add_section(TrackID+"_"+TrackConfigID)
			
			Combo.set(TrackID+"_"+TrackConfigID,CarID,str(current_shutdown_gain))
	else:
		ac.log("Not Found")
	
	with open('apps/python/FFBClip/Config/Combos.ini', 'w') as configfile:
		ac.log("Write")
		Combo.write(configfile)
	if AdaptiveMode != 0 and LearningComplete == 1:
		_persist_combo_lock(LockValue)
		
	if Cutoff > 0.01 and DDToggle==0:
		WriteOptions(FFBClip,FFBClipPath,"targetgains",CarID,str(CarGainTarget+Cutoff))
	else:
		WriteOptions(FFBClip,FFBClipPath,"targetgains",CarID,str(CarGainTarget))
		
	WriteOptions(FFBClip,FFBClipPath,"Options","dynamicmode",str(DynamicMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","maxtorque",str(MaxTorque))
	WriteOptions(FFBClip,FFBClipPath,"Options","targetgain",str(TargetGain))
	WriteOptions(FFBClip,FFBClipPath,"Options","graphrefresh",str(GraphRefresh))
	WriteOptions(FFBClip,FFBClipPath,"Options","displaymode",str(DisplayMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","dynamicthreshold",str(DynamicThreshold))
	WriteOptions(FFBClip,FFBClipPath,"Options","dynamicspeed",str(DynamicSpeed))
	WriteOptions(FFBClip,FFBClipPath,"Options","rb",str(RB))
	WriteOptions(FFBClip,FFBClipPath,"Options","adaptivemode",str(AdaptiveMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","learnlaps",str(LearnLaps))
	WriteOptions(FFBClip,FFBClipPath,"Options","lockpercentile",str(LockPercentile))
	WriteOptions(FFBClip,FFBClipPath,"Options","hybridband",str(HybridBand))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_profilemode",str(FeatureProfileMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_phaselearning",str(FeaturePhaseLearning))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_outlierfilter",str(FeatureOutlierFilter))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_antioscillation",str(FeatureAntiOscillation))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_safetylimits",str(FeatureSafetyLimits))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_autoresetcombo",str(FeatureAutoResetCombo))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_learningconfidence",str(FeatureLearningConfidence))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_endurancemode",str(FeatureEnduranceMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_csvlogging",str(FeatureCSVLogging))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_presetmanager",str(FeaturePresetManager))
	WriteOptions(FFBClip,FFBClipPath,"Options","profilemode",str(ProfileMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","autoprofilesession",str(AutoProfileSession))
	WriteOptions(FFBClip,FFBClipPath,"Options","safetyfloor",str(SafetyFloor))
	WriteOptions(FFBClip,FFBClipPath,"Options","safetyceiling",str(SafetyCeiling))
	WriteOptions(FFBClip,FFBClipPath,"Options","oscillationdeadband",str(OscillationDeadband))
	WriteOptions(FFBClip,FFBClipPath,"Options","oscillationmininterval",str(OscillationMinInterval))
	WriteOptions(FFBClip,FFBClipPath,"Options","enduranceminutes",str(EnduranceMinutes))
	WriteOptions(FFBClip,FFBClipPath,"Options","endurancedropmax",str(EnduranceDropMax))
	WriteOptions(FFBClip,FFBClipPath,"Options","presetname",str(PresetName))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_wetmode",str(FeatureWetMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_kerbfilter",str(FeatureKerbFilter))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_setupawarelearning",str(FeatureSetupAwareLearning))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_confidencegate",str(FeatureConfidenceGate))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_rollbackoneclick",str(FeatureRollbackOneClick))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_responsecurves",str(FeatureResponseCurves))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_advancedantifatigue",str(FeatureAdvancedAntiFatigue))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_diagnosticdashboard",str(FeatureDiagnosticDashboard))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_calibrationassistant",str(FeatureCalibrationAssistant))
	WriteOptions(FFBClip,FFBClipPath,"Options","feature_sessionreport",str(FeatureSessionReport))
	WriteOptions(FFBClip,FFBClipPath,"Options","wetgripthreshold",str(WetGripThreshold))
	WriteOptions(FFBClip,FFBClipPath,"Options","wetsoftening",str(WetSoftening))
	WriteOptions(FFBClip,FFBClipPath,"Options","kerbspikethreshold",str(KerbSpikeThreshold))
	WriteOptions(FFBClip,FFBClipPath,"Options","kerbdampfactor",str(KerbDampFactor))
	WriteOptions(FFBClip,FFBClipPath,"Options","confidencegatethreshold",str(ConfidenceGateThreshold))
	WriteOptions(FFBClip,FFBClipPath,"Options","responsecurvemode",str(ResponseCurveMode))
	WriteOptions(FFBClip,FFBClipPath,"Options","responsecurvestrength",str(ResponseCurveStrength))
	WriteOptions(FFBClip,FFBClipPath,"Options","antifatiguelowband",str(AntiFatigueLowBand))
	WriteOptions(FFBClip,FFBClipPath,"Options","antifatiguehighband",str(AntiFatigueHighBand))
	WriteOptions(FFBClip,FFBClipPath,"Options","antifatiguereduction",str(AntiFatigueReduction))
	WriteOptions(FFBClip,FFBClipPath,"Options","diagrefreshseconds",str(DiagRefreshSeconds))
	WriteOptions(FFBClip,FFBClipPath,"Options","calibrationstate",str(CalibrationState))
	WriteOptions(FFBClip,FFBClipPath,"Options","calibrationwarmuplaps",str(CalibrationWarmupLaps))
	WriteOptions(FFBClip,FFBClipPath,"Options","calibrationlearnlaps",str(CalibrationLearnLaps))
	WriteOptions(FFBClip,FFBClipPath,"Options","calibrationvalidationlaps",str(CalibrationValidationLaps))
	WriteOptions(FFBClip,FFBClipPath,"Options","sessionreportpath",str(SessionReportPath))
	if FeatureSessionReport==1:
		_maybe_write_session_report()
	if FeaturePresetManager==1:
		_save_preset_snapshot()
	
	if AutoMode==0:
		WriteOptions(FFBClip,FFBClipPath,"Options","manualoverride","1")
	else:
		WriteOptions(FFBClip,FFBClipPath,"Options","manualoverride","0")
	
	WriteOptions(FFBClip,FFBClipPath,"Options","ddtoggle",str(DDToggle))
	WriteOptions(FFBClip,FFBClipPath,"Options","ddmappingversion",str(DDMappingVersion))
	
	ac.log("## FFBClip section end")
	
def ReadOptions(File, FilePath, Section, Option, Default):
	
	File.read(FilePath)
	
	if File.has_section(Section):
		#ac.log(Section + " section found")
		if File.has_option(Section,Option):
			#ac.log("ReadOptions: " + Option + " found in " + FilePath)
			ReturnValue = File.get(Section,Option)
			ac.log("ReadOptions: " + Option + ": " + ReturnValue)
		else:
			#ac.log("ReadOptions: " + Option + " not found in " + FilePath)
			File.set(Section,Option,Default)
			ReturnValue=Default
			ac.log("ReadOptions: " + Option + "="+Default + " created in " + FilePath)
	else:
		#ac.log("ReadOptions: " + Section + " not found, creating")
		File.add_section(Section)
		#ac.log("ReadOptions: " + Section + " section created in " + FilePath)
		File.set(Section,Option,Default)
		ReturnValue=Default
		ac.log("ReadOptions: " + Option + "=" + Default + " created in " + FilePath)
			
	with open(FilePath, 'w') as configfile:
		#ac.log("ReadOptions: " + FilePath + " write")
		File.write(configfile)
		
	return str(ReturnValue)
			
def WriteOptions(File, FilePath, Section, Option, Value):


		
	#ac.log("WriteOption") #Debug
	
	File.read(FilePath)
	
	ac.log("Write "+ Section + "-" + Option + " = " + Value )
	if not File.has_section(Section):
		File.add_section(Section)
	if File.has_option(Section,Option):
		File.remove_option(Section, Option)
	File.set(Section, Option, Value)
		
	with open(FilePath, 'w') as configfile:
		#ac.log("Config Write")
		File.write(configfile)
	#ac.log("Close config file")
	
	return ""


def _persist_gain_settings():
	global FFBClip, FFBClipPath, CarID, CarGainTarget, Cutoff, MaxTorque, TargetGain, DDToggle, DDMappingVersion

	if not FFBClipPath:
		return
	if CarID != "":
		stored_target = CarGainTarget + Cutoff if Cutoff > 0.01 and DDToggle == 0 else CarGainTarget
		WriteOptions(FFBClip, FFBClipPath, "targetgains", CarID, str(stored_target))
	WriteOptions(FFBClip, FFBClipPath, "Options", "maxtorque", str(MaxTorque))
	WriteOptions(FFBClip, FFBClipPath, "Options", "targetgain", str(TargetGain))
	WriteOptions(FFBClip, FFBClipPath, "Options", "ddtoggle", str(DDToggle))
	WriteOptions(FFBClip, FFBClipPath, "Options", "ddmappingversion", str(DDMappingVersion))
	
def targetChange(value):
	global errorMessage,messageLabel,CarGainTarget,Cutoff,targetGainSpinner,MaxTorque,DDToggle,AutoMode
	
	ac.console("TargetChange:" + str(value))
	if DDToggle==1:
		CarGainTarget = _dd_nm_to_ratio(value)
		Cutoff=0.05
		msg = "Average cornering torque {}Nm".format(round(value)) if AutoMode == 1 else "Manual override, clipping is NOT prevented"
		_set_message_if_changed(msg)
		_refresh_ui_text()
		_persist_gain_settings()
		ac.console("Cargaintarget: " + str(CarGainTarget) + " - Cutoff: " + str(Cutoff))
		return
		
	if value>100:
		Cutoff=((value/100)-1)
		CarGainTarget=1
		msg = "FFB strength {:.0%}, some clipping allowed".format(value/100) if AutoMode == 1 else "Manual override, clipping is NOT prevented"
	else:
		Cutoff=0.01
		CarGainTarget=(value/100)
		msg = "FFB strength {:.0%}, clipping prevented".format(CarGainTarget) if AutoMode == 1 else "Manual override, clipping is NOT prevented"
			
	_set_message_if_changed(msg)
	_refresh_ui_text()
	_persist_gain_settings()
		
	ac.console("Cargaintarget: " + str(CarGainTarget) + " - Cutoff: " + str(Cutoff))
	
def ResetChange(val1,val2):
	global Histogram,ffbMultiplier,TargetGain,OldCarGain,CarGainCombo

	del Histogram[:]
		
	for n in range(0,300):
		Histogram.append(0)
	
	
	ffbMultiplier=1
	CarGain=round(ac.getCarFFB()/100,2)	
	ffbMultiplier=round(ffbMultiplier,2)
	resetGain = _clamp(TargetGain, 0.0, 3.0)
	if round(resetGain,2) != CarGain:
		_apply_car_gain_target(resetGain)
	reset_value = _dd_ratio_to_nm(TargetGain) if DDToggle == 1 else TargetGain*100
	targetChange(reset_value)
	ac.setValue(targetGainSpinner,reset_value)
	OldCarGain=CarGainCombo
	
	_set_message_if_changed("Reset to default target")
	_refresh_ui_text()
	
def DynamicChange(val1, val2):
	global DynamicMode, DynamicButton
	
	if DynamicMode==1:
		DynamicMode=0
		ResetChange(0,0)
		ac.console("Dynamicmode=0")
	else:
		DynamicMode=1
		ac.console("Dynamicmode=1")
	_refresh_ui_text()
	
	
		
def OptionsChange(val1, val2):
	_set_options_page(OptionsPage == 0)
		
def ManualToggleChange(val1, val2):
	global AutoMode,messageLabel
	
	AutoMode = 0 if val2 else 1
	if AutoMode==1:
		ac.console("Automode on")
		_set_message_if_changed("Auto mode engaged")
	else:
		ac.console("Automode off")
		_set_message_if_changed("Manual override, clipping is NOT prevented")
	_refresh_ui_text()


def AutoModeButtonChange(val1, val2):
	global AutoMode
	AutoMode = 0 if AutoMode == 1 else 1
	ac.setValue(ManualToggle, 1 if AutoMode == 0 else 0)
	if AutoMode == 1:
		_set_message_if_changed("Auto mode engaged")
	else:
		_set_message_if_changed("Manual override, clipping is NOT prevented")
	_refresh_ui_text()
		
def DDToggleButtonChange(val1, val2):
	global DDToggle,targetGainSpinner,TorqueSpinner,OptionsPage,DefaultGainSpinner,DefaultgainSpinnerLabel,StrengthLabel,TargetGain,CarGainTarget,MaxTorque
	
	ac.console("DDToggle:" + str(DDToggleButton))
	DDToggle = 1 if val2 else 0
	_sync_gain_controls()
	targetChange(_target_spinner_value())
	_persist_gain_settings()
	ac.console("DDmode engaged" if DDToggle == 1 else "DDmode disengaged")
	ac.console("DDmode button finished")
	_refresh_ui_text()
	
def RBToggleChange(val1, val2):
	
	global RB
	
	RB = 1 if val2 else 0
	
def TorqueChange(value):

	global MaxTorque,DefaultGainSpinner,TorqueSpinner,targetGainSpinner,TargetGain,CarGainTarget
	
	ac.console("TorqueChange:" + str(value))
	MaxTorque = value
	_sync_gain_controls()
	targetChange(_target_spinner_value())
	DefaultGainChange(_default_spinner_value())
	_persist_gain_settings()
	
	
def DefaultGainChange(value):
	
	global MaxTorque,DDToggle,TargetGain,DefaultGainSpinner
	
	ac.console("DefaultGainChange:" + str(value))
	
	if DDToggle==1:
		TargetGain=_dd_nm_to_ratio(value)
		ac.setRange(DefaultGainSpinner,3,50)
	else:
		TargetGain = value/100
		ac.setRange(DefaultGainSpinner,10,120)
	_refresh_ui_text()
	_persist_gain_settings()
		
def GraphRefreshChange(value):

	global GraphRefresh
	
	GraphRefresh=value
	
def DisplaymodeButtonChange(val1, val2):

	global DisplayMode,DisplaymodeButton
	
	DisplayMode += 1
	
	if DisplayMode>2:
		DisplayMode=0
	if DisplayMode == 1:
		DisplayMode=1
	if DisplayMode == 2:
		DisplayMode=2
	_refresh_ui_text()
		
def DynamicThresholdSpinnerChange(value):

	global DynamicThreshold
	
	DynamicThreshold = value/100
		
def DynamicSpeedSpinnerChange(value):

	global DynamicSpeed
	
	DynamicSpeed = value/10000
	


def AdaptiveModeButtonChange(val1, val2):
	global AdaptiveMode, AdaptiveModeButton
	global LearningLapStart, LearningComplete, LearningSamples, LockValue
	AdaptiveMode += 1
	if AdaptiveMode > 2:
		AdaptiveMode = 0
	_reset_learning_state("Adaptive learning reset")
	if AdaptiveMode != 0:
		_load_combo_lock()
	_refresh_ui_text()


def LearnLapsSpinnerChange(value):
	global LearnLaps, LearningLapStart, LearningComplete, LearningSamples
	LearnLaps = int(_clamp(value,1,20))
	_reset_learning_state("Learning laps updated", clear_persisted=True)


def LockPercentileSpinnerChange(value):
	global LockPercentile, LearningLapStart, LearningComplete, LearningSamples
	LockPercentile = _clamp(value,1,50)
	_reset_learning_state("Lock percentile updated", clear_persisted=True)


def HybridBandSpinnerChange(value):
	global HybridBand
	HybridBand = _clamp(value/100.0,0.05,0.50)
	_reset_learning_state("Hybrid band updated", clear_persisted=True)


def ConfidenceGateSpinnerChange(value):
	global ConfidenceGateThreshold
	ConfidenceGateThreshold = _clamp(value/100.0,0.50,0.98)


def ProfileModeButtonChange(val1, val2):
	global ProfileMode, AutoProfileSession
	AutoProfileSession = 0
	ac.setValue(AutoProfileToggle,0)
	ProfileMode = 0 if ProfileMode == 1 else 1
	_refresh_ui_text()


def OptionsTabDriveChange(val1, val2):
	_show_option_tab(0)


def OptionsTabAdaptiveChange(val1, val2):
	_show_option_tab(1)


def OptionsTabProtectionChange(val1, val2):
	_show_option_tab(2)


def OptionsTabToolsChange(val1, val2):
	_show_option_tab(3)


def CalibrationButtonChange(val1, val2):
	_toggle_calibration()


def ResetLearningButtonChange(val1, val2):
	_reset_learning_state("Learning data cleared", clear_persisted=True)
	_refresh_ui_text()


def RollbackButtonChange(val1, val2):
	_apply_rollback()

def FeatureCSVToggleChange(val1, val2):
	global FeatureCSVLogging
	FeatureCSVLogging = 1 if val2 else 0


def FeaturePresetToggleChange(val1, val2):
	global FeaturePresetManager
	FeaturePresetManager = 1 if val2 else 0


def FeatureProfileToggleChange(val1, val2):
	global FeatureProfileMode
	FeatureProfileMode = 1 if val2 else 0


def FeaturePhaseToggleChange(val1, val2):
	global FeaturePhaseLearning
	FeaturePhaseLearning = 1 if val2 else 0
	_reset_learning_state("Phase learning toggled", clear_persisted=True)


def FeatureOutlierToggleChange(val1, val2):
	global FeatureOutlierFilter
	FeatureOutlierFilter = 1 if val2 else 0


def FeatureOscillationToggleChange(val1, val2):
	global FeatureAntiOscillation
	FeatureAntiOscillation = 1 if val2 else 0


def FeatureSafetyToggleChange(val1, val2):
	global FeatureSafetyLimits
	FeatureSafetyLimits = 1 if val2 else 0


def FeatureEnduranceToggleChange(val1, val2):
	global FeatureEnduranceMode
	FeatureEnduranceMode = 1 if val2 else 0


def FeatureLearningToggleChange(val1, val2):
	global FeatureLearningConfidence
	FeatureLearningConfidence = 1 if val2 else 0


def FeatureAutoResetToggleChange(val1, val2):
	global FeatureAutoResetCombo
	FeatureAutoResetCombo = 1 if val2 else 0


def AutoProfileToggleChange(val1, val2):
	global AutoProfileSession
	AutoProfileSession = 1 if val2 else 0
	_refresh_ui_text()


def SafetyFloorSpinnerChange(value):
	global SafetyFloor, SafetyCeiling
	SafetyFloor = _clamp(value/100.0,0.20,1.50)
	if SafetyFloor > SafetyCeiling:
		SafetyCeiling = SafetyFloor
		ac.setValue(SafetyCeilingSpinner,SafetyCeiling*100)
	_refresh_ui_text()


def SafetyCeilingSpinnerChange(value):
	global SafetyFloor, SafetyCeiling
	SafetyCeiling = _clamp(value/100.0,0.80,3.00)
	if SafetyCeiling < SafetyFloor:
		SafetyFloor = SafetyCeiling
		ac.setValue(SafetyFloorSpinner,SafetyFloor*100)
	_refresh_ui_text()


def OscillationDeadbandSpinnerChange(value):
	global OscillationDeadband
	OscillationDeadband = _clamp(value/100.0,0.0,0.20)


def OscillationMinIntervalSpinnerChange(value):
	global OscillationMinInterval
	OscillationMinInterval = _clamp(value/1000.0,0.05,1.00)


def EnduranceMinutesSpinnerChange(value):
	global EnduranceMinutes
	EnduranceMinutes = _clamp(float(value),10.0,240.0)


def EnduranceDropSpinnerChange(value):
	global EnduranceDropMax
	EnduranceDropMax = _clamp(value/100.0,0.0,0.30)


def WetGripSpinnerChange(value):
	global WetGripThreshold
	WetGripThreshold = _clamp(value/100.0,0.60,1.00)


def WetSofteningSpinnerChange(value):
	global WetSoftening
	WetSoftening = _clamp(value/100.0,0.0,0.30)


def KerbSpikeSpinnerChange(value):
	global KerbSpikeThreshold
	KerbSpikeThreshold = _clamp(value/100.0,0.05,0.80)


def KerbDampSpinnerChange(value):
	global KerbDampFactor
	KerbDampFactor = _clamp(value/100.0,0.35,1.00)


def ResponseCurveModeButtonChange(val1, val2):
	global ResponseCurveMode
	ResponseCurveMode += 1
	if ResponseCurveMode > 2:
		ResponseCurveMode = 0
	_refresh_ui_text()


def ResponseCurveStrengthSpinnerChange(value):
	global ResponseCurveStrength
	ResponseCurveStrength = _clamp(value/100.0,0.0,1.0)


def AntiFatigueLowSpinnerChange(value):
	global AntiFatigueLowBand, AntiFatigueHighBand
	AntiFatigueLowBand = _clamp(value/100.0,0.20,0.95)
	if AntiFatigueLowBand > AntiFatigueHighBand:
		AntiFatigueHighBand = AntiFatigueLowBand
		ac.setValue(AntiFatigueHighSpinner,AntiFatigueHighBand*100)


def AntiFatigueHighSpinnerChange(value):
	global AntiFatigueLowBand, AntiFatigueHighBand
	AntiFatigueHighBand = _clamp(value/100.0,0.30,1.00)
	if AntiFatigueHighBand < AntiFatigueLowBand:
		AntiFatigueLowBand = AntiFatigueHighBand
		ac.setValue(AntiFatigueLowSpinner,AntiFatigueLowBand*100)


def AntiFatigueReductionSpinnerChange(value):
	global AntiFatigueReduction
	AntiFatigueReduction = _clamp(value/100.0,0.0,0.35)


def DiagRefreshSpinnerChange(value):
	global DiagRefreshSeconds
	DiagRefreshSeconds = _clamp(value/100.0,0.25,5.0)


def CalibrationWarmupSpinnerChange(value):
	global CalibrationWarmupLaps
	CalibrationWarmupLaps = int(_clamp(value,0,5))


def CalibrationLearnSpinnerChange(value):
	global CalibrationLearnLaps
	CalibrationLearnLaps = int(_clamp(value,1,10))


def CalibrationValidationSpinnerChange(value):
	global CalibrationValidationLaps
	CalibrationValidationLaps = int(_clamp(value,1,10))

def FeatureWetToggleChange(val1, val2):
	global FeatureWetMode
	FeatureWetMode = 1 if val2 else 0
	_refresh_ui_text()

def FeatureKerbToggleChange(val1, val2):
	global FeatureKerbFilter
	FeatureKerbFilter = 1 if val2 else 0
	_refresh_ui_text()

def FeatureSetupToggleChange(val1, val2):
	global FeatureSetupAwareLearning
	FeatureSetupAwareLearning = 1 if val2 else 0

def FeatureConfidenceToggleChange(val1, val2):
	global FeatureConfidenceGate
	FeatureConfidenceGate = 1 if val2 else 0

def FeatureRollbackToggleChange(val1, val2):
	global FeatureRollbackOneClick
	FeatureRollbackOneClick = 1 if val2 else 0

def FeatureCurveToggleChange(val1, val2):
	global FeatureResponseCurves
	FeatureResponseCurves = 1 if val2 else 0
	_refresh_ui_text()

def FeatureFatigueToggleChange(val1, val2):
	global FeatureAdvancedAntiFatigue
	FeatureAdvancedAntiFatigue = 1 if val2 else 0

def FeatureDiagToggleChange(val1, val2):
	global FeatureDiagnosticDashboard
	FeatureDiagnosticDashboard = 1 if val2 else 0
	_refresh_ui_text()

def FeatureCalibToggleChange(val1, val2):
	global FeatureCalibrationAssistant, CalibrationState, CalibrationLapStart
	FeatureCalibrationAssistant = 1 if val2 else 0
	if FeatureCalibrationAssistant == 0:
		CalibrationState = 0
		CalibrationLapStart = -1
	_refresh_ui_text()

def FeatureReportToggleChange(val1, val2):
	global FeatureSessionReport
	FeatureSessionReport = 1 if val2 else 0

def RunAll(deltaT):

	global Version,appWindow
	global messageLabel,gainLabel
	global errorMessage,graph
	global CarGainTarget,ffbMultiplier,Histogram,dT,CarGain,OldCarGain,CurrentForce,OldFFBMultiplier
	global AutoMode,OldGain,Cutoff, DynamicMode, TargetGain,DynamicTarget,MainGain,OldRAW,ffbMultiplierSmooth,ffbMultiplierSmoothOld
	global DynamicThreshold,DynamicSpeed,DynamicAdd,dTG,GraphRefresh,i
	global AdaptiveMode,LearningComplete,LockValue,HybridBand
	global FeatureProfileMode,FeatureOutlierFilter,FeatureAntiOscillation,FeatureSafetyLimits,FeatureAutoResetCombo,FeatureLearningConfidence,FeatureEnduranceMode,FeatureCSVLogging,FeaturePresetManager
	global ProfileMode,AutoProfileSession,SafetyFloor,SafetyCeiling,LastAppliedGainChange,LastGainApplyTime,OscillationDeadband,OscillationMinInterval,LastComboKey
	global FeatureWetMode,FeatureKerbFilter,FeatureSetupAwareLearning,FeatureConfidenceGate,FeatureRollbackOneClick,FeatureResponseCurves,FeatureAdvancedAntiFatigue,FeatureDiagnosticDashboard,FeatureCalibrationAssistant,FeatureSessionReport
	global WetGripThreshold,WetSoftening,KerbSpikeThreshold,KerbDampFactor,SetupHash,ConfidenceGateThreshold,RollbackGain,RollbackLockValue,ResponseCurveMode,ResponseCurveStrength,AntiFatigueLowBand,AntiFatigueHighBand,AntiFatigueReduction,DiagRefreshSeconds,LastDiagTime,RuntimeMinutesEstimate
	global LearningLapStart,LearningSamples,LearningSamplesSlow,LearningSamplesMid,LearningSamplesFast
	global TrackID,TrackConfigID,CarID,RunClock,LastStatusMessage,PeakForceWindow
	
## Runs every frame
	RunClock += deltaT
	
		
	# CurrentForce = abs(ac.getCarState(0,acsys.CS.LastFF))

	# n=int(CurrentForce*200)
	# if n>0 and OldRAW != CurrentForce:
		# a=Histogram.pop(n)
		# if n<(50*MainGain):
			# inc=n/(50*MainGain)
		# else:
			# inc=1	
		# a += inc
		# Histogram.insert(n,a)
		# #ac.console(str(n) + " - " + str(a))
	# OldRAW=CurrentForce
	
	if DynamicMode==1:
		Interval=0.03
	else:
		Interval=0.5
	
	if dT > Interval:
		CarGain=round(ac.getCarFFB()/100,2)
		if FeatureCalibrationAssistant==1:
			_update_calibration_assistant()
		if FeatureAutoResetCombo==1:
			combo_now = TrackID+"_"+TrackConfigID+"::"+CarID
			if combo_now != LastComboKey:
				_reset_learning_state()
				if AdaptiveMode != 0:
					_load_combo_lock()
				LastComboKey=combo_now
		if FeatureProfileMode==1 and AutoProfileSession==1:
			_auto_profile_from_session()
		if FeatureSetupAwareLearning==1:
			new_hash = _compute_setup_hash()
			if new_hash != SetupHash:
				_reset_learning_state()
				if AdaptiveMode != 0:
					_load_combo_lock()
				SetupHash = new_hash
		isLearningAdaptive = AdaptiveMode != 0 and LearningComplete == 0
		
		windowPeakForce = max(CurrentForce, PeakForceWindow)
		signalForce = max(0.0, windowPeakForce)
		clipLimit = _clamp(CarGainTarget, 0.05, 1.20)
		peakIsClipping = signalForce > (clipLimit * 1.005)
		if isLearningAdaptive:
			ffbMultiplier = _compute_learning_gain_target(CarGain, signalForce, clipLimit)
		else:
			HMax = max(Histogram)+1
			for i in range(299,1,-1):
				if (Histogram[i]/HMax) > Cutoff:
					sample_force = max((i/200.0), 0.05)
					ffbMultiplier = CarGain * (CarGainTarget / sample_force)
					break
			if HMax < (CarGainCombo*100):
				if ffbMultiplier>CarGainCombo:
					ffbMultiplier=CarGainCombo
			if HMax < 200 and HMax > (CarGainCombo*100):
				if ffbMultiplier > (HMax/100):
					ffbMultiplier=HMax/100

			if peakIsClipping:
				peakSafeMultiplier = _compute_peak_safe_gain(CarGain, signalForce, clipLimit)
				ffbMultiplier = min(ffbMultiplier, peakSafeMultiplier)

			if DynamicMode==1:
				if peakIsClipping:
					DynamicAdd=0
				else:
					ffbMultiplier=ffbMultiplier+DynamicAdd
				DynamicAdd = DynamicAdd+DynamicSpeed
		
		allow_gain_shaping = (AdaptiveMode == 0) or (AdaptiveMode == 2 and LearningComplete == 1)
		ffbMultiplier=round(ffbMultiplier,2)
		if FeatureOutlierFilter==1 and allow_gain_shaping:
			ffbMultiplier=_robust_outlier_filter(ffbMultiplier)
		if FeatureProfileMode==1 and allow_gain_shaping:
			# apply mild profile shaping each cycle
			if ProfileMode==1:
				ffbMultiplier = ffbMultiplier * 1.03
			else:
				ffbMultiplier = ffbMultiplier * 0.98
		if FeatureWetMode==1 and allow_gain_shaping:
			ffbMultiplier = _apply_wet_softening(ffbMultiplier)
		if FeatureKerbFilter==1 and allow_gain_shaping:
			ffbMultiplier = _apply_kerb_filter(ffbMultiplier, CurrentForce)
		if FeatureResponseCurves==1 and allow_gain_shaping:
			ffbMultiplier = _apply_response_curve(ffbMultiplier)

		lockSafetyTriggered = False
		# Advanced adaptive modes
		if AdaptiveMode == 1 and LearningComplete == 1:
			# LOCK: stay on learned value, but if a real clip still appears, lower and persist a safer lock.
			ffbMultiplier = LockValue
			if peakIsClipping and AutoMode == 1:
				safe_lock = _clamp(_compute_peak_safe_gain(max(CarGain, LockValue), signalForce, clipLimit) * 0.99, 0.20, 3.0)
				if safe_lock < LockValue:
					LockValue = safe_lock
					RollbackGain = LockValue
					RollbackLockValue = LockValue
					_persist_combo_lock(LockValue)
				ffbMultiplier = LockValue
				lockSafetyTriggered = True
		elif AdaptiveMode == 2 and LearningComplete == 1:
			# HYBRID: blend learned lock and live adaptation, but only force extra drop on real clipping.
			if FeatureConfidenceGate==0 or _confidence_gate_passed():
				low = LockValue * (1.0 - HybridBand)
				high = LockValue * (1.0 + HybridBand)
				ffbMultiplier = _clamp((ffbMultiplier * 0.45) + (LockValue * 0.55), low, high)
				if peakIsClipping:
					ffbMultiplier = min(ffbMultiplier, _compute_peak_safe_gain(CarGain, signalForce, clipLimit))
			elif FeatureRollbackOneClick==1:
				ffbMultiplier = RollbackGain
		if isLearningAdaptive:
			if ffbMultiplier < ffbMultiplierSmoothOld:
				smoothFactor = 0.65
			else:
				smoothFactor = 0.22
			ffbMultiplierSmooth=(ffbMultiplier*smoothFactor)+(ffbMultiplierSmoothOld*(1.0-smoothFactor))
		elif AdaptiveMode == 1 and LearningComplete == 1:
			ffbMultiplierSmooth = LockValue
		elif DynamicMode==0:
			if ffbMultiplier > 3:
				ffbMultiplier=3
				CarGain=3
			# React faster when we need to lower force, slower when bringing it back up.
			if ffbMultiplier < ffbMultiplierSmoothOld:
				smoothFactor = 0.55 if peakIsClipping else 0.25
			else:
				smoothFactor = 0.10
			ffbMultiplierSmooth=(ffbMultiplier*smoothFactor)+(ffbMultiplierSmoothOld*(1.0-smoothFactor))
		else:
			if ffbMultiplier > DynamicThreshold:
				ffbMultiplier=DynamicThreshold
				CarGain=DynamicThreshold
			ffbMultiplierSmooth=ffbMultiplier
		
		if FeatureSafetyLimits==1:
			ce = SafetyCeiling
			if FeatureEnduranceMode==1:
				ce = _apply_endurance_ceiling(ce)
			ffbMultiplierSmooth = _clamp(ffbMultiplierSmooth,SafetyFloor,ce)
		if FeatureAdvancedAntiFatigue==1 and allow_gain_shaping:
			x = ffbMultiplierSmooth
			if x >= AntiFatigueLowBand and x <= AntiFatigueHighBand:
				ffbMultiplierSmooth = x * (1.0 - _clamp(AntiFatigueReduction,0.0,0.35))
		if AdaptiveMode == 1 and LearningComplete == 1:
			ffbMultiplier = LockValue
			ffbMultiplierSmooth = LockValue

		if AutoMode==1:
			DesiredCarGain = _clamp(ffbMultiplierSmooth, 0.0, 3.0)
			GainChange=DesiredCarGain-CarGain
			#ac.log("GainChange: " + str(GainChange))
		else:
			GainChange=OldGain-CarGain
			Change=CarGain/OldGain
			OldGain=CarGain
					
		if GainChange != 0:# and AutoMode==1:

			if FeatureAntiOscillation==1 and not lockSafetyTriggered:
				too_small = abs(GainChange) < OscillationDeadband
				too_fast = (RunClock - LastGainApplyTime) < OscillationMinInterval
				if too_small or too_fast:
					GainChange = 0

			if AutoMode==1 and GainChange != 0:
				Change=ffbMultiplier/CarGain if CarGain>0 else 1
				_apply_car_gain_target(DesiredCarGain)
				LastAppliedGainChange = GainChange
				LastGainApplyTime = RunClock

		AppliedCarGain = round(ac.getCarFFB()/100,2)
		learningFinishedNow = False
		if AdaptiveMode != 0:
			safe_cap_sample = _compute_peak_safe_gain(CarGain, signalForce, clipLimit)
			learningFinishedNow = _update_learning_state(DesiredCarGain if AutoMode==1 else CarGain, safe_cap_sample)
		if learningFinishedNow and AdaptiveMode == 1 and AutoMode == 1:
			ffbMultiplier = LockValue
			ffbMultiplierSmooth = LockValue
			DesiredCarGain = LockValue
			_apply_car_gain_target(LockValue)
			AppliedCarGain = round(ac.getCarFFB()/100,2)
		
		OldCarGain=AppliedCarGain
		ffbMultiplierSmoothOld=ffbMultiplierSmooth
		conf_value = _learning_confidence()
		conf_txt = ""
		if FeatureLearningConfidence==1:
			conf_txt = " | conf {:.0%}".format(conf_value)
		diag_txt=""
		if FeatureDiagnosticDashboard==1 and ((RunClock - LastDiagTime) >= DiagRefreshSeconds):
			diag_txt = " | " + _diag_line(ffbMultiplier,ffbMultiplierSmooth,AppliedCarGain,conf_value)
			LastDiagTime = RunClock
		_set_message_if_changed("Gain T/S/A: {:.0%}/{:.0%}/{:.0%} | {}{}{}".format(ffbMultiplier,ffbMultiplierSmooth,AppliedCarGain,_learning_status_text(),conf_txt,diag_txt))
		_refresh_ui_text()
		if FeatureCSVLogging==1:
			_csv_log_line(ffbMultiplier,ffbMultiplierSmooth,AppliedCarGain)
		
		PeakForceWindow = 0.0
		dT=0
		
	
		
