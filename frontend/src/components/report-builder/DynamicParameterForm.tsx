import { useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Calendar, Info } from 'lucide-react';
import type { ParameterDefinition } from '../../types/report';

interface DynamicParameterFormProps {
  parameterDefinitions: Record<string, ParameterDefinition>;
  uiSchema?: Record<string, any>;
  initialValues?: Record<string, any>;
  onSubmit: (values: Record<string, any>) => void;
  onChange?: (values: Record<string, any>) => void;
  submitLabel?: string;
}

export default function DynamicParameterForm({
  parameterDefinitions,
  uiSchema = {},
  initialValues = {},
  onSubmit,
  onChange,
  submitLabel = 'Submit',
}: DynamicParameterFormProps) {
  // Build Zod schema from parameter definitions
  const buildZodSchema = () => {
    const schemaFields: Record<string, any> = {};

    Object.entries(parameterDefinitions).forEach(([key, def]) => {
      let fieldSchema: any;

      switch (def.type) {
        case 'string':
          fieldSchema = z.string();
          if (def.pattern) {
            fieldSchema = fieldSchema.regex(new RegExp(def.pattern));
          }
          break;
        case 'number':
          fieldSchema = z.number();
          if (def.min !== undefined) {
            fieldSchema = fieldSchema.min(def.min, {
              message: `${def.label} must be greater than or equal to ${def.min}`,
            });
          }
          if (def.max !== undefined) {
            fieldSchema = fieldSchema.max(def.max, {
              message: `${def.label} must be less than or equal to ${def.max}`,
            });
          }
          break;
        case 'date':
          fieldSchema = z.string();
          break;
        case 'boolean':
          fieldSchema = z.boolean();
          break;
        case 'array':
          fieldSchema = z.array(z.string());
          break;
        case 'select':
          fieldSchema = z.string();
          break;
        default:
          fieldSchema = z.any();
      }

      if (def.required) {
        schemaFields[key] = fieldSchema;
      } else {
        schemaFields[key] = fieldSchema.optional();
      }
    });

    // Add date range validation if both start and end dates exist
    const schema = z.object(schemaFields);
    if (schemaFields.start_date && schemaFields.end_date) {
      return schema.refine(
        (data) => {
          if (data.start_date && data.end_date) {
            return new Date(data.end_date) >= new Date(data.start_date);
          }
          return true;
        },
        {
          message: 'End date must be after start date',
          path: ['end_date'],
        }
      );
    }

    return schema;
  };

  const schema = buildZodSchema();

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      ...Object.keys(parameterDefinitions).reduce((acc, key) => {
        const def = parameterDefinitions[key];
        if (def.type === 'boolean') {
          acc[key] = false;
        } else if (def.type === 'array') {
          acc[key] = [];
        } else if (def.default !== undefined) {
          acc[key] = def.default;
        }
        return acc;
      }, {} as Record<string, any>),
      ...initialValues,
    },
  });

  // Watch form values and notify parent
  const watchedValues = watch();
  useEffect(() => {
    if (onChange) {
      onChange(watchedValues);
    }
  }, [watchedValues, onChange]);

  // Get field order from UI schema or use natural order
  const fieldOrder = uiSchema['ui:order'] || Object.keys(parameterDefinitions);

  const renderField = (key: string, def: ParameterDefinition) => {
    const fieldUiSchema = uiSchema[key] || {};
    const placeholder = fieldUiSchema['ui:placeholder'] || `Enter ${def.label.toLowerCase()}`;

    return (
      <div key={key} className="space-y-1">
        <label htmlFor={key} className="block text-sm font-medium text-gray-700">
          {def.label}
          {def.required && <span className="text-red-500 ml-1">*</span>}
        </label>

        <Controller
          name={key}
          control={control}
          render={({ field }) => {
            switch (def.type) {
              case 'string':
                return (
                  <input
                    {...field}
                    type="text"
                    id={key}
                    placeholder={placeholder}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                             focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                );

              case 'number':
                return (
                  <input
                    {...field}
                    type="number"
                    id={key}
                    placeholder={placeholder}
                    min={def.min}
                    max={def.max}
                    onChange={(e) => field.onChange(e.target.valueAsNumber)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                             focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                );

              case 'date':
                return (
                  <div className="relative">
                    <input
                      {...field}
                      type="date"
                      id={key}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md text-sm
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                  </div>
                );

              case 'boolean':
                return (
                  <div className="flex items-center">
                    <input
                      {...field}
                      type="checkbox"
                      id={key}
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded
                               focus:ring-indigo-500"
                    />
                    <label htmlFor={key} className="ml-2 text-sm text-gray-700">
                      {def.description || def.label}
                    </label>
                  </div>
                );

              case 'select':
                return (
                  <select
                    {...field}
                    id={key}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                             focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">{placeholder}</option>
                    {def.options?.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                );

              case 'array':
                const widget = fieldUiSchema['ui:widget'] || 'multiselect';
                if (widget === 'multiselect' && def.options) {
                  return (
                    <select
                      {...field}
                      id={key}
                      multiple
                      value={field.value || []}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, (option) => option.value);
                        field.onChange(selected);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      {def.options.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  );
                }
                // TODO: Add support for tag input or other array widgets
                return null;

              default:
                return null;
            }
          }}
        />

        {def.description && !['boolean'].includes(def.type) && (
          <p className="text-xs text-gray-500 flex items-start gap-1">
            <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
            {def.description}
          </p>
        )}

        {errors[key] && (
          <p className="text-xs text-red-600">
            {errors[key]?.message || `${def.label} is required`}
          </p>
        )}
      </div>
    );
  };

  const onFormSubmit = (data: Record<string, any>) => {
    // Clean up undefined values
    const cleanedData = Object.entries(data).reduce((acc, [key, value]) => {
      if (value !== undefined) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, any>);

    onSubmit(cleanedData);
  };

  const hasRequiredFields = Object.values(parameterDefinitions).some((def) => def.required);

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
      {fieldOrder.map((key: string) => {
        const def = parameterDefinitions[key];
        if (!def) return null;
        return renderField(key, def);
      })}

      {Object.keys(errors).length > 0 && hasRequiredFields && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <p className="text-sm text-red-800">Please fill in all required parameters</p>
        </div>
      )}

      <button
        type="submit"
        className="w-full px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md
                 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        {submitLabel}
      </button>
    </form>
  );
}