<# 
----------------------------------------------------------------------------

Created:      Paul Bullock
Date:         XX/XX/2024
Disclaimer:   

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

.Synopsis

.Example

.Notes

Useful reference: 
      List any useful references

 ----------------------------------------------------------------------------
#>

[CmdletBinding()]
param (
)
begin {

    $sourceFile = "$(Get-Location)\..\README.md"
    

    # ------------------------------------------------------------------------------
    # Introduction
    # ------------------------------------------------------------------------------

    Write-Host @"

 ██████╗ ██████╗ ██████╗ ██╗██╗      ██████╗ ████████╗    ██████╗ ██████╗  ██████╗     ██████╗ ███████╗██╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝    ██╔══██╗██╔══██╗██╔═══██╗    ██╔══██╗██╔════╝██║   ██║
██║     ██║   ██║██████╔╝██║██║     ██║   ██║   ██║       ██████╔╝██████╔╝██║   ██║    ██║  ██║█████╗  ██║   ██║
██║     ██║   ██║██╔═══╝ ██║██║     ██║   ██║   ██║       ██╔═══╝ ██╔══██╗██║   ██║    ██║  ██║██╔══╝  ╚██╗ ██╔╝
╚██████╗╚██████╔╝██║     ██║███████╗╚██████╔╝   ██║       ██║     ██║  ██║╚██████╔╝    ██████╔╝███████╗ ╚████╔╝ 
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝       ╚═╝     ╚═╝  ╚═╝ ╚═════╝     ╚═════╝ ╚══════╝  ╚═══╝  

                        ███████╗ █████╗ ███╗   ███╗██████╗ ██╗     ███████╗███████╗
                        ██╔════╝██╔══██╗████╗ ████║██╔══██╗██║     ██╔════╝██╔════╝
                        ███████╗███████║██╔████╔██║██████╔╝██║     █████╗  ███████╗
                        ╚════██║██╔══██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝  ╚════██║
                        ███████║██║  ██║██║ ╚═╝ ██║██║     ███████╗███████╗███████║
                        ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝╚══════╝                                                                                                        
"@

    Write-Host " Welcome to Copilot Pro Dev Samples, this script will generate a list of samples" -ForegroundColor Green
    
    # ------------------------------------------------------------------------------


    # Validate the source file exists
    if (-Not (Test-Path -Path $sourceFile)) {
        Write-Error "Source file '$sourceFile' does not exist. Exiting script."
        exit
    }

    $BaseDir = "$(Get-Location)\.."
    $assetsFolder = "assets"
    $samplesFolderName = "samples"
    $content = Get-Content -Path $sourceFile -Raw
   
    $OutputSamplesFile = "samples.json"


}
process {

    # ------------------------------------------------------------------------------
    # Generate a consolidated list of samples from the Samples folder
    # ------------------------------------------------------------------------------
    function GetJsonFromSampleJson {
        param(
            [string]$SamplePath,
            [string]$DefaultReturn
        )

        try {
            $assetsFolder = Join-Path -Path $SamplePath -ChildPath $AssetsFolder
            $sampleFilePath = Join-Path -Path $assetsFolder -ChildPath "sample.json"

            $json = Get-Content $sampleFilePath | ConvertFrom-Json

            return $json

        }
        catch {
            # Swallow - this shouldnt happen
            Write-Host "Warning cannot resolve json: $PSItem.Message"
        }

        return $DefaultReturn
    }

    $dir = Join-Path -Path $BaseDir -ChildPath $samplesFolderName
    $files = Get-ChildItem -Path $dir -Recurse -Include README.md

    Write-Host "$($files.Length) found"

    $consolidatedSamplesFile = @()

    $files | Foreach-Object {

        Write-Host "Processing $($_.Directory.Name)"

        # Skip these
        if ($_.Directory.Name -eq "scripts" -or
            $_.Directory.Name -eq "_SAMPLE_templates" -or
            $_.Directory.Name -eq "any-sample" -or
            $_.Directory.Name -eq "dotnet-sample" -or
            $_.Directory.Name -eq "node-sample" -or
            $_.Directory.Name -eq "ttk-vs-code-sample" -or
            $_.Directory.Name -eq "ttk-vs-sample" -or
            $_.Directory.Name -eq "yoteams-sample") {
            return
        }

        $sampleJsonObj = GetJsonFromSampleJson -SamplePath $_.Directory -DefaultReturn $_.Directory.Name
    
        # Remove LongDescription and Description from the sampleJsonObj
        $sampleJsonObj.PSObject.Properties.Remove("LongDescription")
        $sampleJsonObj.PSObject.Properties.Remove("References")
        $sampleJsonObj.PSObject.Properties.Remove("Source")

        $consolidatedSamplesFile += $sampleJsonObj
    }

    # Output Report
    $consolidatedSamplesFile | ConvertTo-Json -Depth 10 | Out-File $OutputSamplesFile -Force
    
    Write-Host "Output written to $OutputSamplesFile" -ForegroundColor Green


    # ------------------------------------------------------------------------------
    # Generate a table list of samples from the Samples folder
    # ------------------------------------------------------------------------------

    <#
        <!-- begin_sample_list -->
        | Title | Description | Author |
        |-------|-------------|--------|
        <!-- begin_sample_list -->
    #>

    $reportContents = @()

    $consolidatedSamplesFile | ForEach-Object{
        $reportContents += "| $($_.Title) | $($_.ShortDescription) | $($_.Authors.Name -join ',') |" 
    }



    # The content of <!-- begin_sample_list --> to <!-- end_sample_list --> will be replaced
    # Use singleline mode so '.' matches newlines (the sample list block may span multiple lines)
    $pattern = '(?s)(<!-- begin_sample_list -->)(.*?)(<!-- end_sample_list -->)'
    $replacement = @'
<!-- begin_sample_list -->
| Title | Description | Author |
|-------|-------------|--------|

'@ + ($reportContents -join "`n") + @'
<!-- end_sample_list -->
'@

    
    $sampleFiles = Get-ChildItem -Path "$(Get-Location)\Samples" -Filter "sample.json" -Recurse



    # Replace the content between the markers (use Singleline option as an extra safeguard)
    $content = [regex]::Replace($content, $pattern, $replacement, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    Write-Host " Replaced content between markers." -ForegroundColor Green

    # Temp write output file called "Readme-Test.md"
    # Copy the Readme.md to Readme-Test.md
    Copy-Item -Path "$(Get-Location)\..\README.md" -Destination "$(Get-Location)\..\README-Test.md"
    $tempOutputFile = "$(Get-Location)\..\README-Test.md"
    Set-Content -Path $tempOutputFile -Value $content

}
end {

    Write-Host "Done! :)" -ForegroundColor Green    
}