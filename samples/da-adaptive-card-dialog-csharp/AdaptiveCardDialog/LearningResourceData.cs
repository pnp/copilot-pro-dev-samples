// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

using AdaptiveCardDialog.Models;

namespace AdaptiveCardDialog
{
    public class LearningResourceData
    {
        public static List<LearningResourceModel> GetResources()
        {
            return new List<LearningResourceModel>
            {
                new() {
                    Id = "1",
                    Topic = "Introduction to Node.js",
                    Description = "Learn Node.js fundamentals - runtime, modules, and server basics from Microsoft",
                    Level = "Beginner",
                    Duration = "8 minutes",
                    VideoId = "FeJVdCz_uco"
                },
                new() {
                    Id = "2",
                    Topic = "JavaScript Fundamentals",
                    Description = "Master JavaScript core concepts with Microsoft's Beginner's Series",
                    Level = "Beginner",
                    Duration = "8 minutes",
                    VideoId = "_EDM5aPVLmo"
                },
                new() {
                    Id = "3",
                    Topic = "Git and GitHub Basics",
                    Description = "Introduction to Git version control from Microsoft Developer",
                    Level = "Beginner",
                    Duration = "6 minutes",
                    VideoId = "9uGS1ak_FGg"
                }
            };
        }
    }
}
