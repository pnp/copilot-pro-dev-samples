using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Helpers
{
    public class EnumHelper
    {
        public static bool TryGetEnumValueFromDisplayName<TEnum>(string displayName, out TEnum enumValue) where TEnum : struct
        {
            foreach (var field in typeof(TEnum).GetFields())
            {
                var attribute = Attribute.GetCustomAttribute(field, typeof(DisplayAttribute)) as DisplayAttribute;
                if (attribute?.Name != null && attribute.Name.Equals(displayName, StringComparison.OrdinalIgnoreCase))
                {
                    if (field.GetValue(null) is TEnum value)
                    {
                        enumValue = value;
                        return true;
                    }
                }
            }
            enumValue = default;
            return false;
        }

        //Get Display name of Enum
        public static string GetDisplayName<TEnum>(TEnum value) where TEnum : struct
        {
            var field = value.GetType().GetField(value.ToString());
            var attribute = Attribute.GetCustomAttribute(field, typeof(DisplayAttribute)) as DisplayAttribute;
            return attribute?.Name ?? value.ToString();
        }

    }
}
