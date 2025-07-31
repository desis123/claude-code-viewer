# Deployment Guide for Claude Code Viewer

## 📋 Pre-requisites

### GitHub Setup
1. Create a new repository on GitHub named `claude-code-viewer`
2. Copy the GitHub URL (will be something like: `https://github.com/desis123/claude-code-viewer.git`)

### PyPI Setup  
1. Create account on [PyPI](https://pypi.org/account/register/)
2. Enable 2FA on your PyPI account
3. Create an API token:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/#api-tokens)
   - Click "Add API token"
   - Name: `claude-code-viewer`
   - Scope: "Entire account" (for first upload)
   - Copy the token (starts with `pypi-`)

## 🚀 Step-by-Step Deployment

### 1. Update Repository URLs

Edit these files and replace `desis123` with your actual GitHub username:

**Files to update:**
- `setup.py` (line 15 and 16)
- `pyproject.toml` (URLs section)
- `README.md` (GitHub links)

```bash
# Find and replace in all files
sed -i 's/desis123/YOUR_GITHUB_USERNAME/g' setup.py pyproject.toml README.md
```

### 2. Initialize Git Repository

```bash
cd /path/to/claude-code-viewer
git init
git add .
git commit -m "Initial release of Claude Code Viewer v1.0.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/claude-code-viewer.git
git push -u origin main
```

### 3. Upload to PyPI

**Option A: Using twine directly**
```bash
# Configure PyPI token (run once)
pip install keyring
keyring set https://upload.pypi.org/legacy/ __token__

# When prompted, enter your PyPI token (the one starting with pypi-)

# Upload to PyPI
twine upload dist/*
```

**Option B: Test on TestPyPI first (recommended)**
```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ claude-code-viewer

# If everything works, upload to real PyPI
twine upload dist/*
```

### 4. Verify Installation

After uploading to PyPI, test the installation:

```bash
# Create a fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# or: test_env\Scripts\activate  # Windows

# Install from PyPI
pip install claude-code-viewer

# Test it
claude-viewer --version
claude-viewer --help
```

## 🏷️ Creating Releases

### For Future Updates

1. **Update version** in `setup.py` and `pyproject.toml`
2. **Update CHANGELOG.md** with new features
3. **Commit and tag**:
   ```bash
   git add .
   git commit -m "Release v1.1.0"
   git tag v1.1.0
   git push origin main --tags
   ```
4. **Rebuild and upload**:
   ```bash
   rm -rf dist/ build/
   python -m build
   twine upload dist/*
   ```

### GitHub Releases

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"  
3. Tag: `v1.0.0`
4. Title: `Claude Code Viewer v1.0.0`
5. Description: Copy from CHANGELOG.md
6. Attach the `.whl` and `.tar.gz` files from `dist/`

## 🔧 Automatic Releases (Optional)

The included GitHub Actions workflow (`.github/workflows/ci.yml`) will automatically:
- Test the code on multiple Python versions
- Build and upload to PyPI when you create a GitHub release

**To enable automatic PyPI uploads:**
1. Go to your GitHub repository → Settings → Secrets → Actions
2. Add secret: `PYPI_API_TOKEN` with your PyPI token as the value
3. Create a GitHub release, and it will auto-upload to PyPI

## 📊 Post-Release Checklist

- [ ] Verify package appears on [PyPI](https://pypi.org/project/claude-code-viewer/)
- [ ] Test installation with `pip install claude-code-viewer`
- [ ] Update social media / community posts
- [ ] Monitor for any issues or bug reports

## 🐛 Troubleshooting

### "Package already exists"
If you get this error, you need to increment the version number in `setup.py` and `pyproject.toml`.

### "Invalid credentials"  
Make sure your PyPI token is correctly set up:
```bash
keyring get https://upload.pypi.org/legacy/ __token__
```

### "README not rendering"
Make sure your README.md is valid Markdown and all image links are absolute URLs.

## 📈 Success Metrics

After release, you can track:
- **PyPI Downloads**: https://pypistats.org/packages/claude-code-viewer
- **GitHub Stars**: Repository popularity
- **Issues/PRs**: Community engagement
- **Usage Analytics**: Through GitHub traffic insights

---

**You're all set! 🎉** 

Your Claude Code Viewer package is ready for the open source community!