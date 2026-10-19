# Giới hạn hiện tại

- 22 logical roles của readiness chưa có; 14 roles đủ recipe R0 cũng thiếu. Không có full reproduction, quality gain hoặc submission ready.
- Các task partial/deferred được liệt kê đầy đủ trong IMPLEMENTATION_STATUS; không suy `done` từ sự tồn tại của file.
- Official evaluator thiếu tokenizer/hash/spec và duplicate semantics. Chỉ có local metrics/LCS diagnostic. Feedback archive bị quarantine, không là qrels.
- Protected exact matcher chưa hiểu negation/quan hệ/intent. Có đủ entities vẫn có thể trả lời sai câu hỏi. Không tự gán medical correctness.
- External dense-index→native-offset adapter, metadata tags và translation provenance mở rộng chưa đủ; không dùng best_idx chưa verified để chọn chunk.
- V1 chỉ sắp/chọn VI, giữ nguyên non-VI slots. PLARGE không có extra VI thì không tạo selection headroom. Source claims complete/provenance phải do handover xác minh.
- Feature job dùng query shards/batch<=900, nhưng refs của một batch và source rankings vẫn nằm RAM. Partial restart recompute, không append; chưa benchmark RAM/I/O hoặc chứng nhận scale toàn corpus.
- F0/L1 tuning đã có orchestration. A1 production bị chặn vì chưa có O0/headroom/negative controls. C1/C2 mới là pure selectors, C3/sparse/discovery chưa được kích hoạt.
- Có guard holdout một lần trên filesystem local. Không phải cơ chế chống người dùng sửa file/đổi protocol; contamination vẫn cần review bằng người.
- Chi phí LZMA dictionary768MiB chưa benchmark. Chỉ --execute/--export mới tạo ZIP; không chạy compression trong kiểm tra fixture.
- Legacy readonly audit là diagnostic riêng. Final records được kiểm bằng BEAR integrity; các luật lịch sử fail không dẫn tới clean/migrate corpus.
- Config evaluation có hash rỗng là template chưa bind; không thay bằng hash giả. Protocol proposed chưa đủ frozen/confirmatory vì chưa có cost ceiling hoặc dev selection.
