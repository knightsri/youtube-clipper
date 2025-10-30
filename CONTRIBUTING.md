# Contributing to YouTube Media Downloader

Thank you for considering contributing to this project! 🎉

## How to Contribute

### Reporting Bugs

Found a bug? Please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Docker version)
- Relevant logs

### Suggesting Features

Have an idea? Open an issue with:
- Clear description of the feature
- Use case / problem it solves
- Potential implementation approach (optional)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/knightsri/youtube-clipper.git
cd youtube-clipper
docker-compose up -d
```

Make changes to `app.py` or `templates/index.html`, then:
```bash
docker-compose restart
```

### Code Style

- Python: Follow PEP 8
- JavaScript: Use consistent indentation
- HTML/CSS: Keep it clean and readable
- Comments: Explain "why", not "what"

### Testing

Before submitting:
- Test basic download functionality
- Test clip extraction
- Test merge functionality
- Check UI on desktop and mobile
- Review console for errors

## Questions?

Open an issue or reach out on GitHub!

---

**Thank you for making this project better!** ❤️