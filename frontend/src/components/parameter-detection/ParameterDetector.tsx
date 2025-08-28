import { useEffect, useState, useMemo } from 'react';
import { ParameterDetector as Detector, debounce } from '../../utils/parameterDetection';
import type { DetectedParameter } from '../../utils/parameterDetection';
import type { FC } from 'react';

interface ParameterDetectorProps {
  sqlQuery: string;
  onParametersDetected: (parameters: DetectedParameter[]) => void;
  debounceMs?: number;
}

/**
 * Component that detects parameters in SQL queries and notifies parent
 */
export const ParameterDetector: FC<ParameterDetectorProps> = ({
  sqlQuery,
  onParametersDetected,
  debounceMs = 500
}) => {
  const [detectedParams, setDetectedParams] = useState<DetectedParameter[]>([]);
  const [isDetecting, setIsDetecting] = useState(false);

  // Create debounced detection function
  const debouncedDetect = useMemo(
    () => debounce((query: string) => {
      setIsDetecting(true);
      
      try {
        const parameters = Detector.detectParameters(query);
        setDetectedParams(parameters);
        onParametersDetected(parameters);
      } catch (error) {
        console.error('Error detecting parameters:', error);
        setDetectedParams([]);
        onParametersDetected([]);
      } finally {
        setIsDetecting(false);
      }
    }, debounceMs),
    [debounceMs, onParametersDetected]
  );

  // Detect parameters when SQL query changes
  useEffect(() => {
    if (sqlQuery) {
      debouncedDetect(sqlQuery);
    } else {
      setDetectedParams([]);
      onParametersDetected([]);
    }
  }, [sqlQuery, debouncedDetect, onParametersDetected]);

  // This component doesn't render anything visible
  // It's a logic-only component that detects parameters
  if (!detectedParams.length) {
    return null;
  }

  // Optionally render a small indicator showing detected parameters
  return (
    <div className="text-xs text-gray-500 mt-2">
      {isDetecting ? (
        <span className="animate-pulse">Detecting parameters...</span>
      ) : (
        <span>
          Detected {detectedParams.length} parameter{detectedParams.length !== 1 ? 's' : ''}: {' '}
          {detectedParams.map((p, i) => (
            <span key={i} className="font-mono bg-gray-100 px-1 rounded">
              {p.placeholder}
            </span>
          )).reduce((prev, curr, i) => 
            i === 0 ? [curr] : [...prev, ', ', curr], [] as React.ReactNode[]
          )}
        </span>
      )}
    </div>
  );
};