Space for analysis instances. Each subdirectory here corresponds to separate
analysis, and shall contain:
- config.txt (fixed file name); each line defines one criterion and shall be
  composed of three words separated by at least one space.
  Each word: max. 8 characters each, no spaces, only the following characters
  allowed: letters, _, numbers
  Empty lines and lines with * as first char are allowed (will be ignored).
  The meaning of words:
  * name of the criterion
  * criterion type (either min or max)
  * name of the outcome variable of the core model defining the criterion

During the analysis diverse files are created/updated in the corresponding
subdirectory. Each file stores information that enables continuation of
analysis from the last stage. All these files shall be in future replace by
storing the info in a DB.
