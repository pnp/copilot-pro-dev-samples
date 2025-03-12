using Microsoft.AspNetCore.Http;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ResolveMate.Core.Models
{
    public class QuestionRequest
    {        
        public string? Question { get; set; }
        public IFormFile? FormFile { get; set; }
    }
}
