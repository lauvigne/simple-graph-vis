export interface SunburstNode {
  id: string;
  label: string;
  value?: number;
  children?: SunburstNode[];
  meta?: Record<string, unknown>;
}

export interface SunburstData {
  label: string;
  metric: {
    key: string;
    label: string;
    unit?: string;
  };
  children: SunburstNode[];
}

export interface SunburstSlice {
  id: string;
  label: string;
  value: number;
  depth: number;
  startAngle: number;
  endAngle: number;
  innerRadius: number;
  outerRadius: number;
  angleSpan: number;
  ringThickness: number;
  arcPath: string;
  color: string;
  opacity: number;
  path: string[];
  labelX: number;
  labelY: number;
  labelRotation: number;
  meta: Record<string, unknown>;
}
