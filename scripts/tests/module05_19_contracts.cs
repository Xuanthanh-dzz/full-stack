using AsyncOrderBatch.Application;
using AsyncOrderBatch.Domain;
using AsyncOrderBatch.Infrastructure;
using System.Text.Json;
internal static class Contracts
{
    static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
    static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception
    {try{await action().WaitAsync(TimeSpan.FromSeconds(10));}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
    public static async Task Main()
    {
        var root=Path.GetFullPath("contract-data");var paths=await DemoData.PrepareAsync(root,CancellationToken.None);
        using var processor=new OrderBatchProcessor(1,OrderRules.Validate);int events=0;
        EventHandler<FileProcessedEventArgs> count=(_,_)=>Interlocked.Increment(ref events);processor.FileProcessed+=count;
        var report=await processor.ProcessAsync([paths[2],paths[0],paths[1]],CancellationToken.None);
        Check(report.Succeeded==2&&report.Failed==1&&report.GrandTotal==3650000m&&events==3,"report");
        Check(report.Files[0].FileName=="01-order.json"&&report.Files[2].FileName=="03-order.json","sorted output");
        var invalid=Path.Combine(root,"invalid.json");await File.WriteAllTextAsync(invalid,"{");
        var missing=Path.Combine(root,"missing.json");var nullfile=Path.Combine(root,"null.json");await File.WriteAllTextAsync(nullfile,"null");
        var bad=await processor.ProcessAsync([invalid,missing,nullfile,paths[0]],CancellationToken.None);
        Check(bad.Failed==3&&bad.Succeeded==1&&events==7,"input errors isolated and gate released");
        using var canceled=new CancellationTokenSource();canceled.Cancel();
        var canceledTask=processor.ProcessAsync(paths,canceled.Token);await ThrowsAsync<OperationCanceledException>(()=>canceledTask);
        Check(canceledTask.IsCanceled&&events==7,"cancel became file failure");
        await ThrowsAsync<ArgumentException>(()=>processor.ProcessAsync([paths[0]," "],CancellationToken.None));Check(events==7,"scheduled before validation");
        EventHandler<FileProcessedEventArgs> fail=(_,_)=>throw new InvalidOperationException("subscriber failure");processor.FileProcessed+=fail;
        await ThrowsAsync<InvalidOperationException>(()=>processor.ProcessAsync([paths[0],paths[1]],CancellationToken.None));
        processor.FileProcessed-=fail;
        Check((await processor.ProcessAsync([paths[0]],CancellationToken.None)).Succeeded==1,"permit leaked on event failure");
        using(var broken=new OrderBatchProcessor(1,_=>default))await ThrowsAsync<InvalidOperationException>(()=>broken.ProcessAsync([paths[0]],CancellationToken.None));
        using(var bug=new OrderBatchProcessor(1,_=>throw new NullReferenceException("injected")))await ThrowsAsync<NullReferenceException>(()=>bug.ProcessAsync([paths[0]],CancellationToken.None));
        var overflow=Path.Combine(root,"overflow.json");await File.WriteAllTextAsync(overflow,"{\"orderId\":\"O\",\"lines\":[{\"sku\":\"A\",\"quantity\":2,\"unitPrice\":79228162514264337593543950335}]}");
        var overflowing=await processor.ProcessAsync([overflow],CancellationToken.None);Check(overflowing.Failed==1,"decimal overflow");
        var output=Path.Combine(root,"report.json");await File.WriteAllTextAsync(output,"old-report");
        await ThrowsAsync<OperationCanceledException>(()=>ReportWriter.WriteAsync(report,output,canceled.Token));
        Check(await File.ReadAllTextAsync(output)=="old-report","canceled write replaced old report");
        Check(Directory.GetFiles(root,".*.tmp").Length==0,"canceled write leaked temp");
        var directory=Path.Combine(root,"output-directory");Directory.CreateDirectory(directory);
        await ThrowsAsync<IOException>(()=>ReportWriter.WriteAsync(report,directory,CancellationToken.None));
        Check(Directory.Exists(directory)&&Directory.GetFiles(root,".*.tmp").Length==0,"failed move cleanup");
        await ReportWriter.WriteAsync(report,output,CancellationToken.None);
        using(var json=JsonDocument.Parse(await File.ReadAllTextAsync(output)))Check(json.RootElement.GetProperty("grandTotal").GetDecimal()==3650000m,"report persistence");
        processor.Dispose();processor.Dispose();await ThrowsAsync<ObjectDisposedException>(()=>processor.ProcessAsync(paths,CancellationToken.None));
    }
}
